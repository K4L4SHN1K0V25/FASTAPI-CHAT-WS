import pytest
from auth_utils import hash_password, verify_password, create_access_token, decode_token

def test_password_hashing():
    """Verifica que el hashing con bcrypt funcione y sea seguro."""
    password = "mi_password_secreto"
    hashed = hash_password(password)
    
    # 1. El hash no debe ser igual a la contraseña en texto plano
    assert hashed != password
    # 2. La verificación debe dar True con la contraseña correcta
    assert verify_password(password, hashed) is True
    # 3. La verificación debe dar False con una contraseña errónea
    assert verify_password("incorrecto", hashed) is False

def test_jwt_generation_and_decoding():
    """Verifica que los tokens se firmen y decodifiquen correctamente."""
    payload = {"sub": "joshua_test"}
    token = create_access_token(payload)
    
    # 1. El token no debe estar vacío y debe ser un string
    assert token is not None
    assert isinstance(token, str)
    
    # 2. Al decodificarlo, debe darnos el mismo payload
    decoded = decode_token(token)
    assert decoded is not None
    assert decoded["sub"] == "joshua_test"

def test_invalid_jwt():
    """Verifica que un token alterado o inválido sea rechazado."""
    token_invalido = "un_token_completamente_falso_y_mal_armado"
    decoded = decode_token(token_invalido)
    assert decoded is None