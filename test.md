now could  you implement the login functionality with a admin user,
note:
- admin user will have all permissions to perfom queries, even guardrails can be bypassed by the admin user.
- create separate mmodel files
- expose apis
- Store user in the graph db with in Users Node,with all properties flatten not nested.
- dfault user also should be kept in the current project 
- default user  credentials:[admin, Admin@123]
- and project the chat api
Follow fastapi standards, there should be authentication and authorization mechanism, use token for requests wherever needed