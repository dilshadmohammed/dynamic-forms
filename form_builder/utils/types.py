class TokenType():
    ACCESS = "accessToken"
    REFRESH = "refreshToken"

class FormType:
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    RADIO_BUTTON = "radio_button"
    MULTIPLE_CHOICE = "multiple_choice"
    CHECKBOX = "checkbox"
    DROPDOWN = "dropdown"
    DATE = "date"
    FILE_UPLOAD = "file_upload"
    
    CHOICES = [
        (SHORT_ANSWER, SHORT_ANSWER),
        (LONG_ANSWER, LONG_ANSWER),
        (MULTIPLE_CHOICE, MULTIPLE_CHOICE),
        (RADIO_BUTTON, RADIO_BUTTON),
        (CHECKBOX, CHECKBOX),
        (DROPDOWN, DROPDOWN),
        (DATE, DATE),
        (FILE_UPLOAD, FILE_UPLOAD),
    ]

