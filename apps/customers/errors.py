# tv4: lỗi gốc cho các quy tắc nghiệp vụ quản lý khách hàng
class CustomerServiceError(Exception):
    """Base error for Customer management business rules."""


# tv4: 4.1.1 báo email đã được tài khoản khác dùng
class DuplicateCustomerEmail(CustomerServiceError):
    pass


# tv4: 4.1.1 báo SĐT đã thuộc khách hàng khác
class DuplicateCustomerPhone(CustomerServiceError):
    pass


# tv4: báo không tìm thấy khách hàng (hoặc đã xóa)
class CustomerNotFound(CustomerServiceError):
    pass


# tv4: 4.1.2/4.1.3 chặn thao tác trên khách hàng đã xóa
class CustomerAlreadyDeleted(CustomerServiceError):
    pass


# tv4: 4.1.3 chặn khóa lại tài khoản đang bị khóa
class CustomerAlreadyLocked(CustomerServiceError):
    pass


# tv4: 4.1.3 chặn mở khóa tài khoản đang hoạt động
class CustomerAlreadyActive(CustomerServiceError):
    pass
