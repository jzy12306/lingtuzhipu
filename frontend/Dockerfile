# 使用官方Node.js镜像作为构建阶段
FROM node:18-alpine AS build

# 设置工作目录
WORKDIR /app

# 复制package.json和package-lock.json
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制项目代码
COPY . .

# 构建应用
RUN npm run build

# 使用Nginx作为生产环境服务器
FROM nginx:alpine

# 复制构建产物到Nginx静态目录
COPY --from=build /app/dist /usr/share/nginx/html

# 复制自定义Nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露80端口
EXPOSE 80

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]