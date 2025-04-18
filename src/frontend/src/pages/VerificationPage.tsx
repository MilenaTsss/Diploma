import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { FaArrowLeft } from 'react-icons/fa';

const VerificationPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [phone, setPhone] = useState(() => location.state?.phone || '+79888363930');
  const [code, setCode] = useState('');
  const [timer, setTimer] = useState(30);
  const [isResendDisabled, setIsResendDisabled] = useState(true);

  useEffect(() => {
    if (timer > 0) {
      const interval = setInterval(() => {
        setTimer((prev) => prev - 1);
      }, 1000);
      return () => clearInterval(interval);
    } else {
      setIsResendDisabled(false);
    }
  }, [timer]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Код подтверждения:', code);
    navigate('/user');
  };

  const handleResendCode = () => {
    setTimer(30);
    setIsResendDisabled(true);
    console.log('Повторная отправка кода для:', phone);
  };

  return (
      <div style={styles.container}>
        <button style={styles.backButton} onClick={() => navigate('/login')}>
          <FaArrowLeft style={styles.icon} />
          <span>Изменить номер телефона</span>
        </button>

        <h2 style={styles.title}>Мобильный телефон</h2>
        <p style={styles.phoneNumber}>{phone}</p>

        <h3 style={styles.subtitle}>Код подтверждения</h3>
        <form onSubmit={handleSubmit} style={styles.form}>
          <label htmlFor="code" style={styles.label}>
            Код
          </label>
          <input
              id="code"
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              maxLength={6}
              style={styles.input}
              required
          />
          <p style={styles.helperText}>На телефон выслан код подтверждения</p>
          <button type="submit" style={styles.confirmButton}>
            Подтвердить
          </button>
        </form>

        <button
            style={isResendDisabled ? styles.resendButtonDisabled : styles.resendButton}
            onClick={handleResendCode}
            disabled={isResendDisabled}
        >
          Отправить код повторно
        </button>

        {isResendDisabled && (
            <div style={styles.timerBox}>
          <span style={styles.timerText}>
            ⏳ Отправить код повторно можно через {Math.floor(timer / 60)}:
            {(timer % 60).toString().padStart(2, '0')}
          </span>
            </div>
        )}
      </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100vh',
    width: '100vw',
    backgroundColor: '#fef7fb',
    padding: '20px',
  },
  backButton: {
    display: 'flex',
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: 'transparent',
    border: 'none',
    color: '#5a4478',
    fontSize: '16px',
    cursor: 'pointer',
    marginBottom: '20px',
  },
  icon: {
    marginRight: '8px',
  },
  title: {
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#5a4478',
  },
  phoneNumber: {
    fontSize: '18px',
    marginBottom: '5px',
    color: '#333',
  },
  subtitle: {
    fontSize: '20px',
    fontWeight: 'bold',
    marginTop: '20px',
    color: '#5a4478',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    width: '100%',
  },
  label: {
    fontSize: '14px',
    marginBottom: '5px',
    color: '#555',
  },
  input: {
    width: '280px',
    fontSize: '18px',
    padding: '12px',
    borderRadius: '8px',
    border: '1px solid #ccc',
    backgroundColor: '#ffffff',
    color: '#333333',
    outline: 'none',
    textAlign: 'center',
    marginBottom: '10px',
  },
  helperText: {
    fontSize: '12px',
    color: '#666',
    marginTop: '5px',
  },
  confirmButton: {
    backgroundColor: '#5a4478',
    color: '#ffffff',
    border: 'none',
    padding: '12px 20px',
    borderRadius: '25px',
    cursor: 'pointer',
    fontSize: '16px',
    marginTop: '15px',
    width: '300px',
  },
  resendButton: {
    backgroundColor: '#d7c4ed',
    color: '#5a4478',
    border: 'none',
    padding: '12px 20px',
    borderRadius: '25px',
    cursor: 'pointer',
    fontSize: '16px',
    marginTop: '15px',
    width: '300px',
  },
  resendButtonDisabled: {
    backgroundColor: '#eae0f5',
    color: '#a89bb5',
    border: 'none',
    padding: '12px 20px',
    borderRadius: '25px',
    fontSize: '16px',
    marginTop: '15px',
    width: '300px',
    cursor: 'not-allowed',
  },
  timerBox: {
    marginTop: '10px',
    padding: '10px',
    border: '1px solid #ccc',
    borderRadius: '10px',
    backgroundColor: '#fff',
  },
  timerText: {
    fontSize: '14px',
    color: '#666',
  },
};

export default VerificationPage;