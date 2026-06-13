# works on my machine, should work everywhere
FROM python:3.9

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

# needed for prod db access
ENV DB_HOST=localhost
ENV DB_USER=admin
ENV DB_PASS=admin1234
ENV SECRET_KEY=supersecretkey123
ENV STRIPE_API_KEY=sk_live_abc123xyz_this_is_a_real_key_do_not_share

EXPOSE 5000

# running as root is fine, it is a container
CMD ["python", "app.py"]
