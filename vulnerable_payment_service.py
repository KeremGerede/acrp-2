"""
vulnerable_payment_service.py

Bu dosya yalnızca yerel test / code review agent denemesi için hazırlanmıştır.
Gerçek ödeme sistemi veya gerçek kullanıcı verisiyle kesinlikle kullanılmamalıdır.

Harici paket gerektirmez.

Çalıştırma:
    python vulnerable_payment_service.py

Tarayıcı:
    http://localhost:8060
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json
import sqlite3
import time
import hashlib
import hmac
import os

DB_NAME = "vulnerable_payments.db"

# ZAFİYET-01: Hardcoded payment secret
# Payment secret gibi kritik bilgiler kod içinde tutulmamalıdır.
PAYMENT_SECRET = "payment-secret-123"

# ZAFİYET-02: Test kart verilerinin kod içinde tutulması
# Gerçek sistemde kart bilgisi asla düz metin veya kod içinde saklanmamalıdır.
TEST_CARDS = {
    "4111111111111111": {
        "cvv": "123",
        "owner": "Kerem Test",
        "balance": 10000
    }
}


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            product_id TEXT,
            amount REAL,
            status TEXT,
            created_at INTEGER
        )
    """)

    cursor.execute("DELETE FROM orders")

    conn.commit()
    conn.close()


class VulnerablePaymentHandler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))

    def get_path_and_query(self):
        parsed = urlparse(self.path)
        return parsed.path, parse_qs(parsed.query)

    def do_GET(self):
        path, query = self.get_path_and_query()

        if path == "/":
            return self.send_json({
                "message": "Vulnerable Payment Service is running",
                "routes": [
                    "/create-order?user_id=1&product_id=10&amount=100",
                    "/pay?order_id=1&card=4111111111111111&cvv=123",
                    "/order?id=1",
                    "/refund?order_id=1&amount=100",
                    "/admin/orders?user_id=1",
                    "/debug/sign?data=test",
                    "/config"
                ],
                "warning": "Bu uygulama bilinçli olarak zafiyetlidir."
            })

        if path == "/create-order":
            user_id = query.get("user_id", [""])[0]
            product_id = query.get("product_id", [""])[0]
            amount = query.get("amount", ["0"])[0]

            # ZAFİYET-03: Business Logic Flaw
            # amount için negatif değer veya maksimum limit kontrolü yapılmıyor.
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # ZAFİYET-04: SQL Injection
            # Kullanıcı girdileri doğrudan SQL içine ekleniyor.
            sql = f"""
                INSERT INTO orders (user_id, product_id, amount, status, created_at)
                VALUES ('{user_id}', '{product_id}', {amount}, 'created', {int(time.time())})
            """

            cursor.execute(sql)
            conn.commit()
            order_id = cursor.lastrowid
            conn.close()

            return self.send_json({
                "status": "order_created",
                "order_id": order_id,
                "sql": sql
            })

        if path == "/pay":
            order_id = query.get("order_id", ["0"])[0]
            card = query.get("card", [""])[0]
            cvv = query.get("cvv", [""])[0]

            # ZAFİYET-05: Sensitive Data in URL
            # Kart numarası ve CVV query string içinde taşınıyor. Loglara/browser history'ye düşebilir.

            # ZAFİYET-06: Sensitive Data Logging
            # Kart bilgisi ve CVV log dosyasına yazılıyor.
            with open("payment_attempts.log", "a", encoding="utf-8") as f:
                f.write(f"order_id={order_id}, card={card}, cvv={cvv}\n")

            if card not in TEST_CARDS or TEST_CARDS[card]["cvv"] != cvv:
                return self.send_json({"error": "Payment failed"}, 402)

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # ZAFİYET-07: SQL Injection
            # order_id doğrudan SQL sorgusuna ekleniyor.
            cursor.execute(f"SELECT id, amount, status FROM orders WHERE id = {order_id}")
            order = cursor.fetchone()

            if not order:
                conn.close()
                return self.send_json({"error": "Order not found"}, 404)

            # ZAFİYET-08: Race Condition / Double Payment Risk
            # Aynı sipariş için tekrar ödeme yapılmasını engelleyen güvenli transaction/lock yok.
            cursor.execute(f"UPDATE orders SET status = 'paid' WHERE id = {order_id}")
            conn.commit()
            conn.close()

            return self.send_json({
                "status": "payment_success",

                # ZAFİYET-09: Sensitive Data Exposure
                # Kart numarası response içinde maskelenmeden dönülüyor.
                "card": card,
                "order_id": order_id
            })

        if path == "/order":
            order_id = query.get("id", ["0"])[0]

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # ZAFİYET-10: SQL Injection
            # id parametresi doğrudan sorguya ekleniyor.
            cursor.execute(f"SELECT id, user_id, product_id, amount, status FROM orders WHERE id = {order_id}")
            order = cursor.fetchone()
            conn.close()

            if not order:
                return self.send_json({"error": "Order not found"}, 404)

            # ZAFİYET-11: IDOR / Broken Access Control
            # Siparişin gerçekten mevcut kullanıcıya ait olup olmadığı kontrol edilmiyor.
            return self.send_json({
                "id": order[0],
                "user_id": order[1],
                "product_id": order[2],
                "amount": order[3],
                "status": order[4]
            })

        if path == "/refund":
            order_id = query.get("order_id", ["0"])[0]
            amount = float(query.get("amount", ["0"])[0])

            # ZAFİYET-12: Missing Authentication / Authorization
            # Refund işlemi için admin veya ödeme yetkisi kontrolü yapılmıyor.

            # ZAFİYET-13: Business Logic Flaw
            # Refund miktarı sipariş tutarından büyük olabilir veya negatif verilebilir.
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(f"UPDATE orders SET status = 'refunded' WHERE id = {order_id}")
            conn.commit()
            conn.close()

            return self.send_json({
                "status": "refund_processed",
                "order_id": order_id,
                "refund_amount": amount
            })

        if path == "/admin/orders":
            user_id = query.get("user_id", [""])[0]

            # ZAFİYET-14: Missing Admin Authorization
            # Admin endpointi olmasına rağmen kimlik/rol kontrolü yok.
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # ZAFİYET-15: SQL Injection
            # user_id doğrudan SQL sorgusuna ekleniyor.
            cursor.execute(f"SELECT id, user_id, product_id, amount, status FROM orders WHERE user_id = '{user_id}'")
            rows = cursor.fetchall()
            conn.close()

            return self.send_json({
                "orders": [
                    {
                        "id": row[0],
                        "user_id": row[1],
                        "product_id": row[2],
                        "amount": row[3],
                        "status": row[4]
                    }
                    for row in rows
                ]
            })

        if path == "/debug/sign":
            data = query.get("data", [""])[0]

            # ZAFİYET-16: Weak Signature / Debug Endpoint Exposure
            # İmza üretim endpointi dışarı açık. Ayrıca debug endpoint prod'da olmamalıdır.
            signature = hmac.new(
                PAYMENT_SECRET.encode(),
                data.encode(),
                hashlib.sha1
            ).hexdigest()

            return self.send_json({
                "data": data,
                "signature": signature
            })

        if path == "/config":
            # ZAFİYET-17: Configuration Exposure
            # Payment secret ve sistem bilgileri dışarı açılıyor.
            return self.send_json({
                "payment_secret": PAYMENT_SECRET,
                "db_name": DB_NAME,
                "cwd": os.getcwd()
            })

        return self.send_json({
            # ZAFİYET-18: Verbose Error
            # Bilinmeyen route detayları dışarı veriliyor.
            "error": "Route not found",
            "path": path
        }, 404)


if __name__ == "__main__":
    init_db()

    # ZAFİYET-19: Public Binding
    # 0.0.0.0 tüm ağ arayüzlerinde dinler. Lokal test için 127.0.0.1 tercih edilebilir.
    server = HTTPServer(("0.0.0.0", 8060), VulnerablePaymentHandler)
    print("Vulnerable Payment Service running on http://localhost:8060")
    server.serve_forever()
