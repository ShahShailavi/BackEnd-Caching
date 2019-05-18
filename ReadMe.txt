#List of members

1. Shailavi Shah
2. Sneha Parikh
3. Tamanna Bhatt

#Project 3 for Backend Web Programming
1. Copy the Back-End-MicroService-Using-Load-Balancer folder to the working directory.
2. Install needed modules from Requirements.txt file
3. First of all we need to start nginx and run Procfile using following commands:
          sudo service nginx start             //To start Nginx
          foreman start --formation user=3,comment=3,article=3,tags=3,rssfeed=3
4. We have created only 3 instances for to distribute load among all available 3 server instance.
5. Run py.test to run all the test cases.
6. To generate RSS feed for article summary, comments and tags, implementation is available in bff.py file.
7. All the curl commands are mentioned in curl_commands file.
8. To Generate RSS feed use following curl commands:
          curl -i -H "Content-Type:application/json" -X GET http://localhost/summaryfeed
          curl -i -H "Content-Type:application/json" -X GET http://localhost/commentfeed
          curl -i -H "Content-Type:application/json" -X GET http://localhost/metafeed
