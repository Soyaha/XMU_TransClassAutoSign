# XMU_TransClassAutoSign
灵感来自 KrsMt-0113/XMU-Rollcall-bot_qrCode，(https://github.com/wilinz/fuck_tronclass_sign)等项目
主要添加实现了多地点自动雷达签到和穷举数字签到

- 使用方法

  下载整个仓库，修改config文件的设置。

  把学号密码改成自己的，然后根据自己需求增加减少雷达定位的地点

  再运行main.py文件就可以自动签到了

  需要python3环境，引用的包都在requirements.txt文件里

  下载命令如下
  ```aiignore
  pip install -r requirements.txt
  ```
- 1-4 行分别为：账号、密码、无、雷达签到经纬度。以下为样例：

    ```aiignore
  "username":"学号",
  "password":"密码，就是自己的畅课密码",
  "sendkey": "_这里不动_",
  "locations": [#这边已经提供了翔安的学武西片和体育馆的经纬度，有需要可以自己改
    { "name": "XueWuLou", "latitude": 24.6082, "longitude": 118.3085 },
    { "name": "XiPian", "latitude": 24.6070, "longitude": 118.2953 },
    { "name": "TiYuGuan", "latitude": 24.6141, "longitude": 118.3057 }
  ]
    ```
