# Step 1: Build the React app
FROM node:18 AS build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
# Set API base URL for Docker environment
# Note: We use localhost:8000 because the frontend is served as static files
# and API requests are made from the browser (host machine), not from the container.
# This allows the React app to connect to the backend running on the host's port 8000.
ARG REACT_APP_API_BASE=http://localhost:8000
ENV REACT_APP_API_BASE=$REACT_APP_API_BASE
RUN npm run build

# Step 2: Serve the built app with nginx
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
