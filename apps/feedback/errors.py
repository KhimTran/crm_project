# tv4: lỗi gốc cho các quy tắc nghiệp vụ xử lý phản hồi
class FeedbackServiceError(Exception):
    """Base error for Feedback handling business rules."""


# tv4: 4.1.4 báo không tìm thấy phản hồi
class FeedbackNotFound(FeedbackServiceError):
    pass


# tv4: 4.1.4 chặn chuyển sang trạng thái không hợp lệ
class InvalidFeedbackStatus(FeedbackServiceError):
    pass


# tv4: 4.1.4 bắt buộc có câu trả lời khi chuyển RESOLVED
class FeedbackNoteRequired(FeedbackServiceError):
    pass


# tv4: 4.2.4 chặn gửi phản hồi cho sản phẩm không còn bán
class ProductNotAvailable(FeedbackServiceError):
    pass
