const https = require('https');

// Test Slack webhook
const SLACK_WEBHOOK = process.env.SLACK_WEBHOOK_URL;

function testSlack() {
  const message = '🧪 **TEST MESAJI**\n\nSistem çalışıyor mu?';
  
  const payload = JSON.stringify({ 
    text: message
  });
  
  console.log('📤 Slack\'e test mesajı gönderiliyor...');
  
  const req = https.request(SLACK_WEBHOOK, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(payload)
    }
  }, (res) => {
    let body = '';
    res.on('data', chunk => body += chunk);
    res.on('end', () => {
      console.log('📊 Slack Response Status:', res.statusCode);
      console.log('📊 Slack Response Body:', body);
      
      if (res.statusCode === 200) {
        console.log('✅ Test mesajı başarıyla gönderildi!');
      } else {
        console.log('❌ Test mesajı gönderilemedi!');
      }
    });
  });
  
  req.on('error', (error) => {
    console.error('❌ Slack hatası:', error);
  });
  
  req.write(payload);
  req.end();
}

testSlack();

