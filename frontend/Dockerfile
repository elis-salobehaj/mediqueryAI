# Frontend Dockerfile - Using pre-built dist
FROM nginx:alpine

# Copy pre-built files to nginx
COPY dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
