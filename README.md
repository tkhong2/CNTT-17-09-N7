<h2 align="center">
    <a href="https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin">
    🎓 Faculty of Information Technology (DaiNam University)
    </a>
</h2>
<h2 align="center">
    PLATFORM ERP: HỆ THỐNG QUẢN LÝ KHÁCH HÀNG + CÔNG VIỆC
</h2>
<h3 align="center">
    Trần Khắc Hồng, Hà Tuấn Huy, Vũ Hồng Sơn
</h3>



<div align="center">
    <p align="center">
        <img src="docs/logo/aiotlab_logo.png" alt="AIoTLab Logo" width="170"/>
        <img src="docs/logo/fitdnu_logo.png" alt="AIoTLab Logo" width="180"/>
        <img src="docs/logo/dnu_logo.png" alt="DaiNam University Logo" width="200"/>
    </p>

[![AIoTLab](https://img.shields.io/badge/AIoTLab-green?style=for-the-badge)](https://www.facebook.com/DNUAIoTLab)
[![Faculty of Information Technology](https://img.shields.io/badge/Faculty%20of%20Information%20Technology-blue?style=for-the-badge)](https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin)
[![DaiNam University](https://img.shields.io/badge/DaiNam%20University-orange?style=for-the-badge)](https://dainam.edu.vn)

</div>


# 1. Giới thiệu Hệ thống Quản lý Khách hàng + Công việc

Hệ thống Quản lý Khách hàng + Công việc là một phân hệ ERP được xây dựng nhằm hỗ trợ quản lý tập trung thông tin khách hàng và theo dõi, điều phối công việc một cách hiệu quả. Hệ thống cho phép lưu trữ dữ liệu khách hàng, quản lý tương tác, lịch hẹn, đồng thời hỗ trợ tạo, phân công và giám sát tiến độ công việc. Dựa trên nền tảng Odoo ERP, hệ thống có khả năng mở rộng linh hoạt, đáp ứng nhu cầu quản lý thực tế của doanh nghiệp.

---
# 2. Các công nghệ được sử dụng
<div align="center">

### Hệ điều hành
[![Ubuntu](https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)](https://ubuntu.com/)
### Công nghệ chính
[![Odoo](https://img.shields.io/badge/Odoo-714B67?style=for-the-badge&logo=odoo&logoColor=white)](https://www.odoo.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![XML](https://img.shields.io/badge/XML-FF6600?style=for-the-badge&logo=codeforces&logoColor=white)](https://www.w3.org/XML/)
### Cơ sở dữ liệu
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
</div>



# 3. Giao diện

### Quản lý Nhân viên
![Giao diện Quản lý Nhân viên](docs/images/giao_dien_nhan_vien.png)

### Quản lý Dự án
![Giao diện Quản lý Dự án](docs/images/giao_dien_du_an.png)

### Quản lý Khách hàng
![Giao diện Quản lý Khách hàng](docs/images/giao_dien_khach_hang.png)


# 4. Cài đặt công cụ, môi trường và các thư viện cần thiết

## 4.1. Clone project.
```
git clone https://github.com/tkhong2/CNTT-17-09-N7.git
```
```
cd CNTT-17-09-N7
```

## 4.2. Cài đặt các thư viện cần thiết

Người sử dụng thực thi các lệnh sau đề cài đặt các thư viện cần thiết

```
sudo apt-get install libxml2-dev libxslt-dev libldap2-dev libsasl2-dev libssl-dev python3.10-distutils python3.10-dev build-essential libssl-dev libffi-dev zlib1g-dev python3.10-venv libpq-dev
```
## 4.3. Khởi tạo môi trường ảo.

Thay đổi trình thông dịch sang môi trường ảo và chạy requirements.txt để cài đặt tiếp các thư viện được yêu cầu
```
python3.10 -m venv ./venv
```
```
source venv/bin/activate
```
```
pip3 install -r requirements.txt
```

## 4.4. Setup database

Khởi tạo database trên docker bằng việc thực thi file dockercompose.yml.
```
sudo apt install docker-compose
```
```
sudo docker-compose up -d
```

## 4.5. Setup tham số chạy cho hệ thống

Tạo tệp **odoo.conf** có nội dung như sau:

```
[options]
addons_path = addons
db_host = localhost
db_password = odoo
db_user = odoo
db_port = 5432
xmlrpc_port = 8069
```

## 4.6. Chạy hệ thống và cài đặt các ứng dụng cần thiết

Lệnh chạy
```
python3 odoo-bin.py -c odoo.conf -u all
```


Người sử dụng truy cập theo đường dẫn _http://localhost:8069/_ để đăng nhập vào hệ thống.

Hoàn tất