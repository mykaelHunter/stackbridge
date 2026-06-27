name: Deploy

on:
  push:
    branches:
      - main

jobs:

  build:

    runs-on: ubuntu-latest

    steps:

    - uses: actions/checkout@v4

    - run: docker build -t app .

    - run: echo "Push image"
