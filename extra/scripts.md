- create user
```mongojs
use admin
db.createUser(
  {
    user: "root",
    pwd: "#@!mongodb_admin_passwd^&*",
    roles: [ { role: "userAdminAnyDatabase", db: "admin" } ]
  }
)

use steam_user_net
db.createUser({
  "user": "steam_user",
  "pwd": "#@!steam_user_passwd^&*",
  "roles": [
    {
      "role": "dbOwner",
      "db": "steam_user_net"
    }
  ]
})
```

- dumpdata
```shell script
rm -rf './extra/steam_user_net'
mongodump -d steam_user_net -o './extra/'
```

- restoredata
```shell script
mongorestore -u 'steam_user' -p '#@!steam_user_passwd^&*' --numParallelCollections 1 -d steam_user_net --drop ./extra/steam_user_net
```


- use db

```shell script
mongo --host imlk.top --port 27017 steam_user_net
```

```mongojs
use steam_user_net
db.auth('steam_user', "#@!steam_user_passwd^&*")

```

- neo4j dump
```shell script
neo4j-admin dump --to=./extra/neo4j_kg.dump
```