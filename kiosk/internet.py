import http.client as httplib

# Source: https://stackoverflow.com/questions/3764291/how-can-i-see-if-theres-an-available-and-active-network-connection-in-python
def internet_active() -> bool:
	connection = httplib.HTTPSConnection("8.8.8.8", timeout=5)
	try:
		connection.request("HEAD", "/")
		return True
	except Exception:
		return False
	finally:
		connection.close()

