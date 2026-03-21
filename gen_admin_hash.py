#!/usr/bin/env python3
import bcrypt
password = 'admin'
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
print(hashed.decode())
