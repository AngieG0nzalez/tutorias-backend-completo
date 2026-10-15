from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

class MessageResponse(BaseModel):
    message: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)
    confirm_password: str
    model_config = ConfigDict(extra="forbid")
    @model_validator(mode="after")
    def validate(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Las contraseñas nuevas no coinciden")
        if self.new_password == self.current_password:
            raise ValueError("La contraseña nueva debe ser distinta")
        return self

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20)
    new_password: str = Field(min_length=8, max_length=128)
    confirm_password: str
    @model_validator(mode="after")
    def validate(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Las contraseñas nuevas no coinciden")
        return self

class ChangeEmailRequest(BaseModel):
    new_email: EmailStr
    current_password: str

class ConfirmEmailRequest(BaseModel):
    token: str = Field(min_length=20)

class AdminResetRequest(BaseModel):
    identity_verified: bool
    reason: str = Field(min_length=15, max_length=500)

class AdminResetResponse(BaseModel):
    message: str
    one_time_token: str
    expires_in_minutes: int
