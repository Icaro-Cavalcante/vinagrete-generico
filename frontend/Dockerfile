FROM nginx:alpine

# Remove config padrão do nginx
RUN rm /etc/nginx/conf.d/default.conf

# Copia config customizada
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copia arquivos estáticos do frontend
COPY index.html /usr/share/nginx/html/
COPY script.js  /usr/share/nginx/html/
COPY style.css  /usr/share/nginx/html/

EXPOSE 80
