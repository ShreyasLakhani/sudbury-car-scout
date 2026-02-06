import { useState, useEffect } from 'react'
import { Container, Grid, Card, Text, Badge, Button, Group, Title, LoadingOverlay, Paper, Modal, TextInput, NumberInput } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

function App() {
  const [cars, setCars] = useState([])
  const [chartData, setChartData] = useState([])
  const [loading, setLoading] = useState(true)
  const [opened, { open, close }] = useDisclosure(false)
  const [email, setEmail] = useState('')
  const [targetPrice, setTargetPrice] = useState(20000)
  const [keyword, setKeyword] = useState('')

  // Use environment variable for API URL, fallback to localhost
  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetch(`${API_URL}/cars`)
      .then((res) => res.json())
      .then((data) => {
        setCars(data)
        // Prepare data for the chart
        const validForChart = data
          .map(car => ({
            ...car,
            priceNum: parseInt(car.price.replace(/[$,]/g, '')) || null,
            mileageNum: parseInt(car.mileage.replace(/[km,]/g, '')) || null,
          }))
          .filter(car => car.priceNum > 0 && car.mileageNum > 0)

        setChartData(validForChart)
        setLoading(false)
      })
      .catch((error) => {
        console.error('Error fetching cars:', error)
        setLoading(false)
      })
  }, [API_URL])

  const handleSetAlert = () => {
    fetch(`${API_URL}/alert`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, target_price: targetPrice, keyword })
    }).then(() => {
        alert("Alert Set! We'll email you if a match appears.")
        close()
    })
    .catch((error) => {
        console.error('Error setting alert:', error)
        alert('Failed to set alert. Please try again.')
    })
  }

  return (
    <Container size="xl" py="xl" style={{ backgroundColor: '#f8f9fa', minHeight: '100vh' }}>
      <Group justify="space-between" mb="lg">
        <div>
          <Title order={1}>Sudbury Car Scout AI</Title>
          <Text c="dimmed">Machine Learning Market Analysis • {cars.length} Listings</Text>
        </div>
        <Button onClick={open} variant="gradient" gradient={{ from: 'indigo', to: 'cyan' }}>
            🔔 Set Price Alert
        </Button>
      </Group>

      <LoadingOverlay visible={loading} />

      <Modal opened={opened} onClose={close} title="Get Notified on Price Drops">
        <TextInput label="Email" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} mb="md" />
        <TextInput label="Car Model" placeholder="e.g. Civic" value={keyword} onChange={(e) => setKeyword(e.target.value)} mb="md" />
        <NumberInput label="Notify me below:" value={targetPrice} onChange={setTargetPrice} prefix="$" mb="lg" />
        <Button onClick={handleSetAlert} fullWidth>Activate Alert</Button>
      </Modal>

      <Paper shadow="sm" p="md" mb="xl" radius="md" withBorder>
        <Title order={4} mb="md">AI Valuation Curve</Title>
        <div style={{ height: 400 }}>
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" dataKey="mileageNum" name="Mileage" unit="km" domain={['auto', 'auto']} />
              <YAxis type="number" dataKey="priceNum" name="Price" unit="$" domain={['auto', 'auto']} />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter name="Cars" data={chartData} fill="#228be6" />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </Paper>

      <Grid align="stretch">
        {cars.map((car, index) => (
          <Grid.Col key={index} span={{ base: 12, md: 6, lg: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder h="100%">
              <Group justify="space-between" mt="md" mb="xs">
                <Badge color="blue" variant="light">{car.price}</Badge>
                {car.deal_rating && <Badge color={car.deal_color} variant="filled">{car.deal_rating}</Badge>}
              </Group>

              <Text fw={700} size="lg" lineClamp={2} title={car.title} style={{ minHeight: '50px' }}>
                {car.title}
              </Text>
              <Text size="sm" c="dimmed" mt="sm">Mileage: <b>{car.mileage}</b></Text>

              <Button component="a" href={car.link} target="_blank" fullWidth mt="md" radius="md" variant="filled" color="blue">
                View Listing
              </Button>
            </Card>
          </Grid.Col>
        ))}
      </Grid>
    </Container>
  )
}

export default App