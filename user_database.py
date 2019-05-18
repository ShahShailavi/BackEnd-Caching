from cassandra.cluster import Cluster

cluster = Cluster(['172.17.0.2'])
session = cluster.connect('article_database')

session.execute("""Create COLUMNFAMILY article_blog(
      id INT,
      author text,
      title text,
      content text,
      url text,
      createdDate text,
      modifiedDate text,
      comment text,
      tag text,
      flag text,
      PRIMARY KEY (flag, id)
)WITH CLUSTERING ORDER BY (id DESC);""")

session.execute("""Create COLUMNFAMILY users_table(
      name TEXT,
      username TEXT,
      userpassword TEXT,
      PRIMARY KEY (username)
);""")
