class FeedbackServiceError(Exception):
    """Base error for Feedback handling business rules."""


class FeedbackNotFound(FeedbackServiceError):
    pass


class InvalidFeedbackStatus(FeedbackServiceError):
    pass


class FeedbackNoteRequired(FeedbackServiceError):
    pass


class ProductNotAvailable(FeedbackServiceError):
    pass
