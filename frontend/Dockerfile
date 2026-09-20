# Step 1: Build the React app
FROM node:22-alpine AS build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
# Set API base URL for Docker environment
# Note: We use localhost:8000 because the frontend is served as static files
# and API requests are made from the browser (host machine), not from the container.
# This allows the React app to connect to the backend running on the host's port 8000.
ARG REACT_APP_API_BASE=http://localhost:8000
ENV REACT_APP_API_BASE=$REACT_APP_API_BASE
ARG REACT_APP_BUILD_VERSION=local-container
ENV REACT_APP_BUILD_VERSION=$REACT_APP_BUILD_VERSION
RUN npm run build

# Step 2: Serve the built app with nginx
FROM nginx:1.27-alpine
ARG REACT_APP_API_BASE=http://localhost:8000
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
RUN sed -i "s|__API_ORIGIN__|${REACT_APP_API_BASE}|g" /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
