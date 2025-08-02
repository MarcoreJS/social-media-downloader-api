```bash
curl -X POST "http://localhost:8000/download/" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/reel/DLJdRoJCr6B/?igsh=Z2Q2ZjYxbjh6Y2gz"}'


curl -X POST "http://localhost:8000/download/" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/p/CbLXzSDO7vv9FymElo2kKo_t1Kjc4io76-xgJ40/?igsh=ZDJzbzB2cDZydHE3"}'

curl -X POST "http://localhost:8000/download/" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/p/C-PfMmrSdGa/?igsh=MWNzaWtkOGM5MTFsaQ=="}'

curl -X POST "http://localhost:8000/download/" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/p/DK9Afm1S0QY/?igsh=MWVubzFkemhkejM2Mw=="}'
```