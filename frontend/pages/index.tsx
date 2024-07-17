import React from 'react';
import Head from 'next/head';
import styles from '../styles/Home.module.css';
import Curriculum from '../components/Curriculum';
import Chat from '../components/Chat';

const Home: React.FC = () => {
  return (
    <div className={styles.container}>
      <Head>
        <title>Virtual Curriculum</title>
        <meta name="description" content="Chat with a virtual curriculum powered by Claude AI" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className={styles.main}>
        <h1 className={styles.title}>Welcome to Virtual Curriculum</h1>
        <div className={styles.grid}>
          <Curriculum />
          <Chat />
        </div>
      </main>

      <footer className={styles.footer}>
        <a href="#" target="_blank" rel="noopener noreferrer">
          Powered by Claude AI and Speechify
        </a>
      </footer>
    </div>
  );
};

export default Home;