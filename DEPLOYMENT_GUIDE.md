# Hướng Dẫn Triển Khai (Deployment) Hệ Thống Odoo 18 Lên AWS EC2

> **Dự án:** ARC-ODOO — Hệ thống Quản lý Giao dịch Chứng khoán  
> **Nền tảng:** Amazon Web Services (AWS) EC2  
> **Công nghệ:** Docker, Docker Compose, Nginx, PostgreSQL 17, Odoo 18  
> **Hệ điều hành Server:** Ubuntu 24.04 LTS (x86_64)

> **Lưu ý bảo mật:** Tất cả thông tin nhạy cảm (mật khẩu, địa chỉ IP, khóa bí mật) trong tài liệu này đều sử dụng **giá trị minh họa** (placeholder). Thông tin thực tế được bảo mật và không công khai.

---

## Mục Lục

1. [Tổng Quan Kiến Trúc Triển Khai](#1-tổng-quan-kiến-trúc-triển-khai)
2. [Yêu Cầu Hệ Thống](#2-yêu-cầu-hệ-thống)
3. [Tạo Máy Chủ EC2 Trên AWS](#3-tạo-máy-chủ-ec2-trên-aws)
4. [Cấu Hình Kết Nối SSH](#4-cấu-hình-kết-nối-ssh)
5. [Cài Đặt Môi Trường Server](#5-cài-đặt-môi-trường-server)
6. [Triển Khai Ứng Dụng](#6-triển-khai-ứng-dụng)
7. [Cấu Hình Mạng & Tường Lửa (Security Groups)](#7-cấu-hình-mạng--tường-lửa-security-groups)
8. [Cấu Hình Tên Miền (DNS)](#8-cấu-hình-tên-miền-dns)
9. [Cấu Hình Nginx Reverse Proxy & SSL (Tùy chọn)](#9-cấu-hình-nginx-reverse-proxy--ssl-tùy-chọn)
10. [Kiểm Tra & Xác Minh Hệ Thống](#10-kiểm-tra--xác-minh-hệ-thống)
11. [Xử Lý Sự Cố Thường Gặp](#11-xử-lý-sự-cố-thường-gặp)
12. [Phụ Lục: Cấu Trúc Dự Án](#12-phụ-lục-cấu-trúc-dự-án)

---

## 1. Tổng Quan Kiến Trúc Triển Khai

Hệ thống được triển khai theo mô hình **Container hóa (Containerization)** sử dụng Docker. Toàn bộ ứng dụng được đóng gói thành các container độc lập, đảm bảo tính nhất quán giữa môi trường phát triển (Development) và môi trường sản xuất (Production).

### Sơ Đồ Kiến Trúc

```
                    ┌─────────────────────────────────────────┐
                    │           AWS EC2 Instance               │
                    │          Ubuntu 24.04 LTS                │
                    │         IP: <PUBLIC_IP>                  │
                    │                                          │
  Người dùng ──────►│  ┌──────────────────────────────────┐   │
  (Trình duyệt)    │  │       Docker Compose              │   │
                    │  │                                    │   │
                    │  │  ┌────────────┐  ┌─────────────┐  │   │
                    │  │  │  Odoo 18   │  │ PostgreSQL  │  │   │
                    │  │  │   Server   │──│     17      │  │   │
                    │  │  │ Port 8069  │  │  Port 5432  │  │   │
                    │  │  └────────────┘  └─────────────┘  │   │
                    │  │       ▲                            │   │
                    │  └───────┼────────────────────────────┘   │
                    │          │                                │
                    │    Port 8070 ◄── Mapping ──► Port 8069   │
                    └──────────┼───────────────────────────────┘
                               │
                    http://<PUBLIC_IP>:8070
```

### Thành Phần Hệ Thống

| Thành phần            | Công nghệ               | Vai trò                                         |
| --------------------- | ----------------------- | ----------------------------------------------- |
| **Web Server**        | Odoo 18 (Python)        | Xử lý logic nghiệp vụ, phục vụ giao diện web    |
| **Database**          | PostgreSQL 17           | Lưu trữ dữ liệu người dùng, giao dịch, cấu hình |
| **Container Runtime** | Docker & Docker Compose | Đóng gói và vận hành các dịch vụ                |
| **Cloud Platform**    | AWS EC2                 | Cung cấp máy chủ ảo trên nền tảng đám mây       |
| **Reverse Proxy**     | Nginx (tùy chọn)        | Chuyển tiếp request, cài đặt SSL/HTTPS          |

---

## 2. Yêu Cầu Hệ Thống

### Phần Cứng (AWS EC2 Instance)

| Thông số         | Yêu cầu tối thiểu    | Khuyến nghị      |
| ---------------- | -------------------- | ---------------- |
| **CPU**          | 1 vCPU               | 2 vCPU           |
| **RAM**          | 1 GB (+ 2-4 GB Swap) | 4 GB             |
| **Ổ cứng**       | 20 GB SSD            | 30 GB SSD        |
| **Hệ điều hành** | Ubuntu 22.04+ LTS    | Ubuntu 24.04 LTS |
| **Kiến trúc**    | x86_64 (AMD64)       | x86_64           |

### Phần Mềm

| Phần mềm       | Phiên bản | Mục đích                  |
| -------------- | --------- | ------------------------- |
| Docker         | 24.0+     | Container runtime         |
| Docker Compose | 1.29+     | Điều phối multi-container |
| Git            | 2.34+     | Quản lý mã nguồn          |
| OpenSSH        | 8.9+      | Kết nối từ xa             |

### Tài Khoản & Dịch Vụ

- Tài khoản **AWS** (Free Tier hoặc trả phí)
- Tài khoản **GitHub** (lưu trữ mã nguồn)
- Tên miền (tùy chọn, nếu muốn truy cập bằng domain thay vì IP)

---

## 3. Tạo Máy Chủ EC2 Trên AWS

### Bước 3.1: Đăng nhập AWS Console

Truy cập [https://console.aws.amazon.com/ec2/](https://console.aws.amazon.com/ec2/) và đăng nhập bằng tài khoản AWS.

### Bước 3.2: Khởi tạo Instance

1. Nhấp nút **"Launch Instance"** (Khởi chạy Instance).
2. Điền thông tin cấu hình:

| Mục               | Giá trị                                                    |
| ----------------- | ---------------------------------------------------------- |
| **Name**          | `<TÊN_DỰ_ÁN>` (tên dự án của bạn)                          |
| **AMI**           | Ubuntu Server 24.04 LTS (HVM), SSD Volume Type             |
| **Instance type** | `t2.micro` (Free Tier) hoặc `t3.small`                     |
| **Key pair**      | Tạo mới hoặc chọn key pair có sẵn (tải file `.pem` về máy) |
| **Storage**       | 20 GB gp3 (General Purpose SSD)                            |

3. Tại mục **Network settings**, đảm bảo:
   - Cho phép SSH traffic từ "Anywhere" (0.0.0.0/0).
4. Nhấp **"Launch Instance"** và chờ trạng thái chuyển sang **Running**.

### Bước 3.3: Ghi nhận thông tin kết nối

Sau khi Instance khởi động thành công, ghi lại:

- **Public IPv4 Address**: `<PUBLIC_IP>` (ví dụ: `x.x.x.x`)
- **Private IPv4 Address**: `<PRIVATE_IP>`
- **Instance ID**: `<INSTANCE_ID>`

---

## 4. Cấu Hình Kết Nối SSH

### Bước 4.1: Lưu trữ Private Key

Lưu file Private Key (`.pem`) được tải về từ AWS vào vị trí an toàn trên máy tính cá nhân:

```
C:\Users\<TenNguoiDung>\Downloads\PASS.pem
```

### Bước 4.2: Tạo file SSH Config

Mở hoặc tạo file `C:\Users\<TenNguoiDung>\.ssh\config` và thêm nội dung:

```ssh-config
Host aws-odoo
    HostName <PUBLIC_IP>
    User ubuntu
    IdentityFile C:\Users\<TenNguoiDung>\Downloads\<TÊN_KEY>.pem
```

> **Giải thích:**
>
> - `Host aws-odoo`: Tên gợi nhớ, dùng để gọi tắt khi kết nối SSH.
> - `HostName`: Địa chỉ IP Public của máy chủ EC2.
> - `User`: Tài khoản mặc định của Ubuntu trên AWS.
> - `IdentityFile`: Đường dẫn tới file khóa bí mật (Private Key).

### Bước 4.3: Phân quyền file `.pem` (nếu gặp lỗi UNPROTECTED PRIVATE KEY)

Trên Windows, nếu SSH báo lỗi quyền truy cập file `.pem`:

1. Chuột phải vào file `.pem` → **Properties** → Tab **Security** → **Advanced**.
2. Nhấp **"Disable inheritance"** → Chọn **"Convert inherited permissions..."**.
3. Xóa tất cả người dùng, chỉ giữ lại tài khoản cá nhân với quyền **Full Control**.
4. Nhấp **Apply** → **OK**.

### Bước 4.4: Kết nối SSH

Mở Terminal (PowerShell / CMD) và chạy:

```bash
ssh aws-odoo
```

Lần đầu kết nối, hệ thống hỏi xác nhận fingerprint → gõ `yes` → Enter.

**Kết quả mong đợi:**

```
Welcome to Ubuntu 24.04.3 LTS (GNU/Linux 6.x.x-xxxx-aws x86_64)
ubuntu@ip-<PRIVATE_IP>:~$
```

---

## 5. Cài Đặt Môi Trường Server

> **Lưu ý:** Tất cả các lệnh trong phần này được thực hiện **trên máy chủ Ubuntu** (sau khi đã SSH vào).

### Bước 5.1: Cập nhật hệ thống

```bash
sudo apt update && sudo apt upgrade -y
```

### Bước 5.2: Tạo RAM ảo (Swap)

AWS EC2 Free Tier (t2.micro) chỉ có 1GB RAM. Odoo và PostgreSQL cần nhiều RAM hơn để hoạt động ổn định. Swap file giúp sử dụng ổ cứng làm bộ nhớ mở rộng.

```bash
# Tạo Swap file 4GB
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Cấu hình Swap tự động bật khi khởi động lại server
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

**Kiểm tra:**

```bash
free -h
```

**Kết quả mong đợi:**

```
              total   used   free   shared  buff/cache  available
Mem:          952Mi   ...    ...    ...      ...         ...
Swap:         4.0Gi   ...    ...
```

### Bước 5.3: Cài đặt Docker và Docker Compose

```bash
# Cài đặt Docker Engine và Docker Compose
sudo apt install docker.io docker-compose -y

# Thêm user 'ubuntu' vào nhóm docker (để chạy docker không cần sudo)
sudo usermod -aG docker ubuntu
newgrp docker

# Kiểm tra phiên bản
docker --version
docker-compose --version
```

---

## 6. Triển Khai Ứng Dụng

### Bước 6.1: Clone mã nguồn từ GitHub

```bash
# Tạo thư mục chứa dự án
mkdir -p ~/project && cd ~/project

# Clone mã nguồn
git clone https://github.com/<github-username>/ARC-ODOO.git

# Di chuyển vào thư mục dự án
cd ARC-ODOO
```

### Bước 6.2: Cấu hình quyền thực thi

File `entrypoint.sh` là script khởi tạo của Docker container. Trên Linux, file này cần có quyền thực thi (executable permission):

```bash
# Cấp quyền thực thi cho entrypoint
sudo chmod +x entrypoint.sh

# Tạo thư mục dữ liệu PostgreSQL
sudo mkdir -p postgresql
sudo chmod 777 postgresql
```

### Bước 6.3: Cấu trúc Docker Compose

File `docker-compose.yml` định nghĩa 2 dịch vụ (services):

```yaml
version: "2"
services:
  # Dịch vụ 1: Cơ sở dữ liệu PostgreSQL
  db:
    image: postgres:17
    user: root
    environment:
      - POSTGRES_USER=<DB_USER>
      - POSTGRES_PASSWORD=<DB_PASSWORD>
      - POSTGRES_DB=postgres
    restart: always
    volumes:
      - ./postgresql:/var/lib/postgresql/data

  # Dịch vụ 2: Odoo 18 Application Server
  odoo18:
    image: odoo:18
    user: root
    depends_on:
      - db
    ports:
      - "8070:8069" # Web interface
      - "8072:8072" # Live chat / Longpolling
    tty: true
    command: --
    environment:
      - HOST=db
      - USER=<DB_USER>
      - PASSWORD=<DB_PASSWORD>
      - PIP_BREAK_SYSTEM_PACKAGES=1
    volumes:
      - ./entrypoint.sh:/entrypoint.sh
      - ./addons:/mnt/extra-addons # Custom modules
      - ./tests:/mnt/tests # Unit tests
      - ./etc:/etc/odoo # Cấu hình Odoo
    restart: always
```

> **Giải thích Port Mapping `"8070:8069"`:**
>
> - Cổng `8069` là cổng mặc định của Odoo bên trong container.
> - Cổng `8070` là cổng expose ra bên ngoài để người dùng truy cập qua trình duyệt.
> - Tham số `restart: always` đảm bảo hệ thống tự động khởi động lại nếu server bị restart.

### Bước 6.4: Cài đặt thư viện Python bổ sung

File `entrypoint.sh` tự động cài đặt các thư viện Python được liệt kê trong `etc/requirements.txt` khi container khởi động:

```
# CORE
requests>=2.31.0          # HTTP client
Pillow>=10.0.1            # Image processing

# SSI FASTCONNECT API
ssi-fc-data>=1.0.0        # SSI Market Data SDK
ssi-fctrading>=1.0.0      # SSI Trading SDK

# DATA & ANALYSIS
numpy>=1.24.0             # Numerical computing
pandas>=2.0.0             # Data manipulation

# AI TRADING
finrl                     # FinRL framework
stable-baselines3>=2.0.0  # DRL algorithms
gymnasium>=0.29.0         # RL environments
scikit-learn>=1.3.0       # ML utilities

# PDF & REPORTING
PyMuPDF>=1.23.8           # PDF manipulation
openpyxl>=3.1.2           # Excel export

# UTILITIES
python-dateutil>=2.8.2    # Date parsing
pytz>=2023.3              # Timezone handling
```

### Bước 6.5: Khởi động hệ thống

```bash
# Khởi động tất cả dịch vụ ở chế độ nền (detached mode)
docker-compose up -d
```

Docker sẽ tự động:

1. Tải Docker Image `odoo:18` và `postgres:17` từ Docker Hub.
2. Tạo container cho từng dịch vụ.
3. Chạy `entrypoint.sh` để cài đặt thư viện Python bổ sung.
4. Khởi động Odoo Server trên cổng 8069 (mapping ra 8070).

**Theo dõi quá trình khởi động:**

```bash
docker logs arc-odoo_odoo18_1 -f
```

**Kiểm tra trạng thái container:**

```bash
docker ps
```

**Kết quả mong đợi:**

```
CONTAINER ID  IMAGE        STATUS         PORTS
8bbc211e36bb  odoo:18      Up 11 seconds  0.0.0.0:8070->8069/tcp, 0.0.0.0:8072->8072/tcp
6e6123a7ce9b  postgres:17  Up 1 minute    5432/tcp
```

---

## 7. Cấu Hình Mạng & Tường Lửa (Security Groups)

Mặc định, AWS EC2 chặn tất cả kết nối từ Internet (trừ cổng SSH 22). Cần mở các cổng mạng cần thiết để người dùng truy cập được ứng dụng web.

### Bước 7.1: Mở AWS Console

Truy cập [https://console.aws.amazon.com/ec2/](https://console.aws.amazon.com/ec2/) → **Instances** → Chọn máy chủ.

### Bước 7.2: Chỉnh sửa Security Group

1. Chọn tab **Security** ở phần chi tiết Instance.
2. Nhấp vào tên **Security Group** (dạng `sg-0xxxxx`).
3. Nhấp nút **"Edit inbound rules"**.
4. Thêm các quy tắc (rules) sau:

| Type       | Protocol | Port Range | Source    | Mô tả                        |
| ---------- | -------- | ---------- | --------- | ---------------------------- |
| SSH        | TCP      | 22         | 0.0.0.0/0 | Kết nối SSH (mặc định đã có) |
| Custom TCP | TCP      | **8070**   | 0.0.0.0/0 | Giao diện web Odoo           |
| Custom TCP | TCP      | **8072**   | 0.0.0.0/0 | Odoo Live Chat / Longpolling |
| HTTP       | TCP      | 80         | 0.0.0.0/0 | _(Tùy chọn)_ Nếu cài Nginx   |
| HTTPS      | TCP      | 443        | 0.0.0.0/0 | _(Tùy chọn)_ Nếu cài SSL     |

5. Nhấp **"Save rules"**.

---

## 8. Cấu Hình Tên Miền (DNS)

### Mục đích

Thay vì truy cập qua địa chỉ IP (ví dụ: `http://54.169.29.25:8070`), cấu hình tên miền cho phép người dùng truy cập qua URL dễ nhớ hơn (ví dụ: `http://arccap.vn:8070`).

### Bước 8.1: Đăng ký tên miền

Đăng ký tên miền tại nhà cung cấp dịch vụ tên miền (ví dụ: TenTen, Namecheap, GoDaddy, v.v.).

### Bước 8.2: Cấu hình bản ghi DNS

Truy cập trang quản lý DNS của nhà cung cấp tên miền và tạo bản ghi:

| Tên (Name) | Loại (Type) | Giá trị (Value) | Độ ưu tiên |
| ---------- | ----------- | --------------- | ---------- |
| `@`        | A           | `<PUBLIC_IP>`   | 0          |

> **Giải thích:** Bản ghi **A Record** (Address Record) liên kết tên miền với địa chỉ IP của máy chủ. Khi người dùng gõ tên miền, hệ thống DNS sẽ phân giải thành địa chỉ IP tương ứng.

### Bước 8.3: Chờ DNS cập nhật

DNS cần thời gian phân phối (propagation) trên toàn mạng Internet, thường từ **5 phút đến 24 giờ** tùy nhà cung cấp.

**Kiểm tra:**

```bash
nslookup arccap.vn
```

---

## 9. Cấu Hình Nginx Reverse Proxy & SSL (Tùy chọn)

### Mục đích

- Ẩn số cổng `:8070` khỏi URL (truy cập trực tiếp `https://arccap.vn`).
- Cài đặt chứng chỉ SSL miễn phí (HTTPS, biểu tượng ổ khóa xanh trên trình duyệt).
- Tăng tính bảo mật và chuyên nghiệp cho hệ thống.

### Bước 9.1: Cài đặt Nginx

```bash
sudo apt install nginx -y
```

### Bước 9.2: Tạo file cấu hình Nginx

```bash
sudo nano /etc/nginx/sites-available/odoo
```

Nội dung file:

```nginx
# Chuyển hướng HTTP sang HTTPS
server {
    listen 80;
    server_name <TÊN_MIỀN> www.<TÊN_MIỀN>;
    return 301 https://$host$request_uri;
}

# Cấu hình HTTPS
server {
    listen 443 ssl;
    server_name <TÊN_MIỀN> www.<TÊN_MIỀN>;

    # Chứng chỉ SSL (sẽ được tạo ở bước sau bởi Certbot)
    ssl_certificate /etc/letsencrypt/live/<TÊN_MIỀN>/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/<TÊN_MIỀN>/privkey.pem;

    # Proxy trỏ tới Odoo container
    location / {
        proxy_pass http://127.0.0.1:8070;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Proxy cho Longpolling (Live Chat)
    location /longpolling {
        proxy_pass http://127.0.0.1:8072;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Bước 9.3: Kích hoạt cấu hình

```bash
# Tạo symlink để kích hoạt site
sudo ln -s /etc/nginx/sites-available/odoo /etc/nginx/sites-enabled/

# Xóa cấu hình mặc định
sudo rm /etc/nginx/sites-enabled/default

# Kiểm tra cú pháp
sudo nginx -t

# Khởi động lại Nginx
sudo systemctl restart nginx
```

### Bước 9.4: Cài đặt chứng chỉ SSL miễn phí (Let's Encrypt)

```bash
# Cài đặt Certbot
sudo apt install certbot python3-certbot-nginx -y

# Xin chứng chỉ SSL (thay 'arccap.vn' bằng tên miền thực tế)
sudo certbot --nginx -d <TÊN_MIỀN> -d www.<TÊN_MIỀN>
```

Certbot sẽ tự động:

- Xin chứng chỉ SSL miễn phí từ Let's Encrypt.
- Cập nhật file cấu hình Nginx.
- Thiết lập tự động gia hạn chứng chỉ (mỗi 90 ngày).

---

## 10. Kiểm Tra & Xác Minh Hệ Thống

### Bước 10.1: Kiểm tra trạng thái dịch vụ

```bash
# Kiểm tra Docker containers
docker ps

# Kiểm tra Nginx (nếu đã cài)
sudo systemctl status nginx

# Kiểm tra RAM & Swap
free -h

# Kiểm tra dung lượng ổ cứng
df -h
```

### Bước 10.2: Truy cập giao diện web

| Phương thức                             | URL                       |
| --------------------------------------- | ------------------------- |
| Truy cập bằng IP                        | `http://<PUBLIC_IP>:8070` |
| Truy cập bằng tên miền (không Nginx)    | `http://<TÊN_MIỀN>:8070`  |
| Truy cập bằng tên miền (có Nginx + SSL) | `https://<TÊN_MIỀN>`      |

### Bước 10.3: Tạo Database Odoo

Lần đầu truy cập, Odoo hiển thị trang **Database Manager**:

| Trường              | Giá trị                                               |
| ------------------- | ----------------------------------------------------- |
| **Master Password** | `<MASTER_PASSWORD>` (được cấu hình trong `odoo.conf`) |
| **Database Name**   | Tên cơ sở dữ liệu (ví dụ: `arc_production`)           |
| **Email**           | Email quản trị viên                                   |
| **Password**        | Mật khẩu tài khoản admin                              |
| **Language**        | Vietnamese / English                                  |
| **Country**         | Vietnam                                               |

---

## 11. Xử Lý Sự Cố Thường Gặp

### 11.1. Lỗi `permission denied: entrypoint.sh`

**Nguyên nhân:** File `entrypoint.sh` bị mất quyền thực thi khi clone từ Git (Windows → Linux).

**Giải pháp:**

```bash
sudo chmod +x entrypoint.sh
docker-compose down && docker-compose up -d
```

### 11.2. Container Odoo liên tục Restart

**Chẩn đoán:**

```bash
docker logs arc-odoo_odoo18_1 --tail 50
```

**Nguyên nhân phổ biến:**

- Thiếu thư viện Python → Kiểm tra `etc/requirements.txt`.
- Lỗi cú pháp trong mã nguồn.
- Hết RAM → Kiểm tra Swap (`free -h`).

### 11.3. Lỗi `502 Bad Gateway` (khi dùng Nginx)

**Nguyên nhân:** Nginx đang chạy nhưng không kết nối được tới Odoo backend.

**Giải pháp:**

```bash
# Kiểm tra Odoo container có đang chạy
docker ps

# Nếu container Exited, restart lại
docker-compose down && docker-compose up -d
```

### 11.4. Không truy cập được web từ trình duyệt

**Nguyên nhân:** Chưa mở port trên AWS Security Group.

**Giải pháp:** Xem lại [Mục 7: Cấu Hình Mạng & Tường Lửa](#7-cấu-hình-mạng--tường-lửa-security-groups).

### 11.5. `pip install` lỗi `externally-managed-environment`

**Nguyên nhân:** Ubuntu 24.04 áp dụng PEP 668, không cho phép cài package Python trực tiếp trên hệ thống.

**Giải pháp:** **Không cài package trên máy chủ Ubuntu.** Các thư viện Python được cài tự động **bên trong Docker container** thông qua `entrypoint.sh`. Biến môi trường `PIP_BREAK_SYSTEM_PACKAGES=1` trong `docker-compose.yml` đã xử lý vấn đề này bên trong container.

---

## 12. Phụ Lục: Cấu Trúc Dự Án

```
ARC-ODOO/
├── addons/                    # Các module Odoo tự phát triển
│   ├── ai_trading_assistant/  # Module AI Trading
│   ├── custom_auth/           # Module xác thực người dùng
│   ├── fund_management/       # Module quản lý quỹ
│   ├── investor_list/         # Module danh sách nhà đầu tư
│   ├── order_matching/        # Module khớp lệnh giao dịch
│   ├── stock_data/            # Module dữ liệu chứng khoán
│   ├── stock_trading/         # Module giao dịch chứng khoán
│   └── ...                    # Các module khác
├── etc/
│   ├── odoo.conf              # File cấu hình Odoo Server
│   └── requirements.txt       # Danh sách thư viện Python bổ sung
├── tests/                     # Unit tests
├── docker-compose.yml         # Định nghĩa dịch vụ Docker
├── entrypoint.sh              # Script khởi tạo container
└── README.md                  # Tài liệu dự án
```

### Các Lệnh Quản Trị Thường Dùng

| Lệnh                               | Mô tả                                    |
| ---------------------------------- | ---------------------------------------- |
| `docker-compose up -d`             | Khởi động hệ thống (chạy nền)            |
| `docker-compose down`              | Dừng toàn bộ hệ thống                    |
| `docker-compose restart`           | Khởi động lại hệ thống                   |
| `docker logs <container> -f`       | Xem log theo thời gian thực              |
| `docker ps`                        | Liệt kê container đang chạy              |
| `docker ps -a`                     | Liệt kê tất cả container (kể cả đã dừng) |
| `docker exec -it <container> bash` | Truy cập vào bên trong container         |

---

> **Tài liệu này được viết phục vụ cho báo cáo đồ án tốt nghiệp.**  
> **Ngày cập nhật:** 26/02/2026
