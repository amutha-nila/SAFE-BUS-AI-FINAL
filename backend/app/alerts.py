def alerts(bus,s):
 state=s['state'];cur=s['current'];cap=s['capacity'];p=[round(x) for x in s['predictions']]
 if state=='SEVERE':
  ta=f'சாமி, பஸ் ஓவர்லோடு ஆச்சு. இப்போ {cur} பேர் இருக்காங்க. கொள்ளளவு {cap} பேர். அடுத்த ஸ்டாப்களிலும் கூட்டம் அதிகரிக்க வாய்ப்பு இருக்கு. கூட்டம் குறையும் வரை யாரையும் உள்ளே ஏத்தாதீங்க. யாராவது கீழே இறங்கினால் மட்டும் புதிய பயணிகளை அனுமதிக்கவும். பஸ்ஸை தானாக நிறுத்த வேண்டாம். Traffic Officer-க்கு தகவல் தெரிவிக்கப்படுகிறது.'
  en=f'Attention. Bus {bus} is overloaded. Current load is {cur} out of {cap}. The ANN predicts approximately {p[0]}, {p[1]} and {p[2]} passengers at the next three stops. Do not allow new passengers to board until the crowd decreases. Allow boarding only when passengers get down. Do not stop the bus automatically. The Traffic Officer is being alerted.'
 elif state=='CRITICAL':
  ta='கவனம். பஸ்ஸில் அதிக நெரிசல் உள்ளது. கூட்டம் குறையும் வரை புதிய பயணிகளை அனுமதிக்க வேண்டாம்.';en=f'Critical crowding detected on bus {bus}. Hold new boarding until the load decreases.'
 elif state=='WARNING':
  ta='கவனம். பஸ்ஸில் கூட்டம் அதிகரித்து வருகிறது. அடுத்த ஸ்டாப்களில் நெரிசல் ஏற்பட வாய்ப்பு உள்ளது.';en=f'Warning. Passenger load is increasing on bus {bus}. Crowding may occur at the next stops.'
 else:
  ta=f'பஸ் பாதுகாப்பான நிலையில் உள்ளது. தற்போது {cur} பயணிகள் உள்ளனர்.';en=f'Bus {bus} is currently within the configured safe load range.'
 return ta,en

def officer(bus,s):return f"Traffic Officer alert: Bus {bus} is in {s['state']} state. Current load {s['current']}/{s['capacity']}. Predicted loads {', '.join(str(round(x)) for x in s['predictions'])}. Human intervention recommended. Automatic bus stopping is disabled."
