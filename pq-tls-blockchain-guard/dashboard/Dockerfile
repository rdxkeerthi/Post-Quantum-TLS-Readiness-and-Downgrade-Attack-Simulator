FROM node:20-alpine
WORKDIR /app
RUN npx create-next-app@latest . --use-npm --no-install --ts --eslint --src-dir --app --no-git --no-tailwindcss
CMD ["npm", "run", "dev", "--", "-p", "3000"]
