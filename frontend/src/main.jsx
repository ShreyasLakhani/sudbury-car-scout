import React from 'react'
import ReactDOM from 'react-dom/client'
import { MantineProvider, createTheme } from '@mantine/core'
import App from './App.jsx'
import '@mantine/core/styles.css'
import './index.css'

const theme = createTheme({
  fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  headings: {
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    fontWeight: '700',
  },
  primaryColor: 'indigo',
  defaultRadius: 'lg',
  colors: {
    dark: [
      '#C9C9C9', // 0
      '#B8B8B8', // 1
      '#828282', // 2
      '#696969', // 3
      '#4A4A4A', // 4
      '#3A3A3A', // 5
      '#2C2C2C', // 6
      '#1F1F1F', // 7
      '#181818', // 8
      '#0F0F0F', // 9
    ],
  },
  components: {
    Card: {
      defaultProps: {
        radius: 'lg',
      },
    },
    Button: {
      defaultProps: {
        radius: 'md',
      },
    },
    Paper: {
      defaultProps: {
        radius: 'lg',
      },
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <MantineProvider theme={theme} defaultColorScheme="dark">
      <App />
    </MantineProvider>
  </React.StrictMode>,
)