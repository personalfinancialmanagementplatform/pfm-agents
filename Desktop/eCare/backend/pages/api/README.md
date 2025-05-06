## API TEST

### Test Login
```
curl -X POST http://localhost:3000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "Juliana", "password": "12345678abc"}'

```

### Test Signup
```
curl -X POST http://localhost:3000/api/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "Juliana",
    "email": "Juliana@example.com",
    "password": "12345678abc"
  }'
```

### Test Logout
```
curl -X POST http://localhost:3000/api/logout \
  -b cookie.txt \
  -c cookie.txt
```