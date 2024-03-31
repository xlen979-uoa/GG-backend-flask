## Deploy the service on Azure with Nginx and gunicorn

1. clone the repository to Azure
```
https://github.com/xlen979-uoa/GG-backend-flask.git
``` 
2. install related packages
```
pip install -r requirements
```
3. test if the service can run successfully (kill the process after it runs scuessfully)
```
python run.py
kill -9 PID (your process id)
```
4. use gunicorn to start the service and test (kill the process after it runs scuessfully)
```
pip install gunicorn 
gunicorn -w 4 -b 127.0.1:5000 run:app
kill -9 PID (your process id)
```
5. install nginx
```
sudo apt install nginx
```
6. set ssl on nginx (you need to apply a ssl certificate for https)
```
vim /etc/nginx/sites-available/default

server {
	listen 443 ssl default_server;
	listen [::]:443 ssl default_server;
	server_name ***; #your domain name;

	ssl on;
	ssl_certificate /etc/ssl/private/***.crt; #public key
	ssl_certificate_key /etc/ssl/private/***.key;   #private key

	location / {
		proxy_pass        http://localhost:5000;
        	proxy_set_header   Host $host;
        	proxy_set_header   X-Real-IP  $remote_addr;
        	proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
		proxy_redirect default;
	}
}

sudo /etc/init.d/nginx restart
```
7. rerun gunicorn
```
sudo nohup gunicorn -w 4 -b 127.0.1:5000 run:app > flask.log  2>&1 &
```


### Reference link 
[Visit](https://www.djangoz.com/2018/03/10/flask_app/)

