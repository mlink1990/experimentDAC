import server
import ADEval

IP_ADRESS = "192.168.16.67"
PORT = 8888

class ADEval_server:
	def __init__(self, PORT = PORT, IP_ADRESS = IP_ADRESS):
		self.PORT = PORT
		self.IP_ADRESS = IP_ADRESS
		#self.spi = None
		#self.LDAC = 11
		#self.SYNC = 13
		self.ADEval = None
		self.Server = None
		self.startADEval()
		self.startServer()


	def startADEval(self):
		print "starting ADEval"
		self.ADEval = ADEval.ADEval()


	def startServer(self):
		print "starting server"
		self.server = server.SocketServer(self.PORT, self.IP_ADRESS)
		self.server.ADEvalReference = self.ADEval

	def closeServer(self):
                print "Closing server"
                self.server.server_close()

if __name__ == "__main__":
        try:
                s = ADEval_server(IP_ADRESS=IP_ADRESS)
        finally:
                s.closeServer()
