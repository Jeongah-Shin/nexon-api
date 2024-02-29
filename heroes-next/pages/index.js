import { useState } from 'react';
import axios from 'axios';

export default function Home() {
  const [nickname, setNickname] = useState('');
  const [server, setServer] = useState('');
  const [responseData, setResponseData] = useState(null);
  const [error, setError] = useState(null);
  const [requestURL, setRequestURL] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const baseUrl = 'https://openapi.nexon.com/maplestorym/v1/id';
      const params = new URLSearchParams({
        nickname: nickname,
        server: server
      }).toString();
      const url = `${baseUrl}?${params}`;
      const headers = {
        'Access-Control-Allow-Origin': '*',
        'x-nxopen-api-key': 'test_2958b9766ef6c3c095523436b152cefca9f05cbc75911515a5096869d59e07e4c842870f9d4db52332e5372aab23070a'
      };
      const response = await axios.get(url, {
        headers: headers
      }, 
      { withCredentials: true });
      setResponseData(response.data);
      setError(null); // 성공한 경우 에러 초기화
      setRequestURL(url); // 요청한 URL 저장
    } catch (error) {
      console.error('Error fetching data:', error);
      setResponseData(null); // 에러 발생 시 응답 데이터 초기화
      setError(error.toString()); // 에러 메시지 설정
      setRequestURL(''); // 요청한 URL 초기화
    }
  };

  return (
    <div>
      <h1>MapleStoryM API 요청</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label>
            닉네임:
            <input type="text" value={nickname} onChange={(e) => setNickname(e.target.value)} />
          </label>
        </div>
        <div>
          <label>
            서버명:
            <select value={server} onChange={(e) => setServer(e.target.value)}>
              <option value="server1">스카니아</option>
              <option value="server2">아케인</option>
              <option value="server3">루나</option>
              {/* 필요한 서버명으로 옵션을 추가하세요 */}
            </select>
          </label>
        </div>
        <button type="submit">데이터 요청</button>
      </form>
      {error && (
        <div style={{ color: 'red' }}>
          <h2>에러 발생:</h2>
          <p>{error}</p>
          {requestURL && (
            <div>
              <h3>요청한 URL:</h3>
              <p>{requestURL}</p>
              <h3>헤더:</h3>
              <pre>{JSON.stringify(headers, null, 2)}</pre>
            </div>
          )}
        </div>
      )}
      {responseData && (
        <div>
          <h2>응답 데이터:</h2>
          <pre>{JSON.stringify(responseData, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}