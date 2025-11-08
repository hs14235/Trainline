import { useEffect, useState } from 'react';
import api from './api';

export default function Profile() {
  const [user, setUser] = useState({});
  useEffect(()=>{
    api.get('user/').then(r=>setUser(r.data));
  },[]);

  const handleSave = e => {
    e.preventDefault();
    api.patch('user/update/', user)
       .then(()=>alert('Profile updated!'));
  };

  return (
    <form onSubmit={handleSave} className="card">
      <h1>My Profile</h1>
      <label>
        First name<br/>
        <input
          value={user.first_name||''}
          onChange={e=>setUser({...user, first_name:e.target.value})}
        />
      </label><br/>
      <label>
        Last name<br/>
        <input
          value={user.last_name||''}
          onChange={e=>setUser({...user, last_name:e.target.value})}
        />
      </label><br/>
      <label>
        Email<br/>
        <input
          value={user.email||''}
          onChange={e=>setUser({...user, email:e.target.value})}
        />
      </label><br/><br/>
      <button type="submit">Save Profile</button>
    </form>
  );
}
