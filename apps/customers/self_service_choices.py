"""TV1 profile choices aligned with TV4's customer input contract.

Source: feature/tv4-models at 2f0b82e (constants/forms). Keep this adapter
separate from TV4's constants module until the branches are integrated.
"""

GENDER_CHOICES = (("MALE", "Nam"), ("FEMALE", "Nữ"), ("OTHER", "Khác"))
PLAYING_LEVEL_CHOICES = (
    ("BEGINNER", "Mới chơi"), ("RECREATIONAL", "Phong trào"), ("COMPETITIVE", "Thi đấu"),
)
CATEGORY_PREFERENCE_TYPE = "CATEGORY"
