from chalice import Chalice

app = Chalice(app_name='test')


@app.on_sns_message("ses_tbxofficial_inbound_email")
def hello(event):
	print("****** PARTY TIME O'CLOCK *****")
