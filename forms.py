from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import InputRequired, Length, Email, DataRequired, EqualTo, Regexp

min_password_len = 6

password_len_message = f"Пароль должен быть больше {min_password_len} символов"
password_required = "Вы не ввели пароль"
password_regex = "Пароль должен иметь по крайней мере 1 букву и цифру"

mail_len_message = f"Длина почтового адреса должна быть больше {min_password_len}"
mail_required = "Вы не заполнили поле почтового адреса"
mail_validate = "Вы ввели неверный формат почты"


class LoginForm(FlaskForm):
    mail = EmailField('mail', validators=[Length(min=min_password_len, max=100, message=mail_len_message),
                                          Email(message=mail_validate),
                                          InputRequired(message=mail_required)],
                      render_kw={"placeholder": "Email"})

    password = PasswordField('password', validators=[Length(min=min_password_len, max=100,
                                                     message=password_len_message),
                                                     InputRequired(message=password_required),
                                                     Regexp(regex="^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{"+
                                                                  str(min_password_len)+",}$", message=password_regex)],
                             render_kw={"placeholder": "Пароль"})


class RegistrationForm(FlaskForm):
    name = StringField('name', validators=[Length(min=1, max=50, message="Имя не должн превышать 50 символов"),
                                           InputRequired(message="Вы не заполнили поле с именем")],
                       render_kw={"placeholder": "Имя"})

    mail = StringField('mail', validators=[Length(min=min_password_len, max=100, message=mail_len_message),
                                           Email(message=mail_validate),
                                           InputRequired(message=mail_required)],
                       render_kw={"placeholder": "Email"})

    password = PasswordField('password', validators=[Length(min=min_password_len, max=100,
                                                     message=password_len_message),
                                                     InputRequired(message=password_required),
                                                     EqualTo('confirm', message="Пароли не совпадают"),
                                                     Regexp(regex="^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{" +
                                                                  str(min_password_len) + ",}$", message=password_regex)
                                                     ])

    confirm = PasswordField('confirm', validators=[InputRequired(message=password_required)])
