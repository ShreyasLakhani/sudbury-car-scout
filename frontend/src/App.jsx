import { useState, useEffect } from 'react'
import { Container, Grid, Card, Text, Badge, Button, Group, Title, LoadingOverlay, Paper } from '@mantine/core'
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Label } from 'recharts'

function App() {
  const [cars, setCars] = useState([])
  const [chartData, setChartData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('http://localhost:8000/cars')
      .then((res) => res.json())
      .then((data) => {
        setCars(data)
        
        // Prepare Chart Data
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
        console.error("Error:", error)
        setLoading(false)
      })
  }, [])

  return (
    <Container size="xl" py="xl" style={{ backgroundColor: '#f8f9fa', minHeight: '100vh' }}>
      <Group justify="space-between" mb="lg">
        <div>
          <Title order={1}>Sudbury Car Scout</Title>
          <Text c="dimmed">AI-Powered Market Analysis • {cars.length} Listings</Text>
        </div>
        <Button component="a" href="http://localhost:8000/cars" target="_blank" variant="outline" color="gray">
            Raw Data API
        </Button>
      </Group>

      <LoadingOverlay visible={loading} />

      {/* ANALYTICS SECTION */}
      <Paper shadow="sm" p="md" mb="xl" radius="md" withBorder>
        <Title order={4} mb="md">Market Value Analysis</Title>
        <div style={{ height: 400 }}>
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 100 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" dataKey="mileageNum" name="Mileage" unit="km" domain={['auto', 'auto']}>
                <Label value="Mileage (km)" offset={-10} position="insideBottom" style={{ textAnchor: 'middle', fontWeight: 'bold' }} />
              </XAxis>
              
              <YAxis type="number" dataKey="priceNum" name="Price" unit="$" domain={['auto', 'auto']}>
                 <Label 
                   value="Price ($)" 
                   angle={-90} 
                   position="center" 
                   dx={-40}
                   style={{ textAnchor: 'middle', fontWeight: 'bold' }} 
                 />
              </YAxis>
              
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter name="Cars" data={chartData} fill="#228be6" />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
        <Text size="sm" c="dimmed" mt="xs" ta="center">
          *Dots lower on the graph represent better value (Price vs Mileage).
        </Text>
      </Paper>

      {/* LISTING GRID */}
      <Grid align="stretch">
        {cars.map((car, index) => (
          <Grid.Col key={index} span={{ base: 12, md: 6, lg: 4 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder h="100%" style={{ display: 'flex', flexDirection: 'column' }}>
              
              {/* Header: Price + Deal Badge */}
              <Group justify="space-between" mb="xs">
                <Badge color="blue" variant="light">{car.price}</Badge>
                {car.deal_rating && (
                    <Badge color={car.deal_color} variant="filled">{car.deal_rating}</Badge>
                )}
              </Group>

              <Text fw={700} size="lg" lineClamp={2} title={car.title} style={{ minHeight: '50px' }}>
                {car.title}
              </Text>

              <Text size="sm" c="dimmed" mt="sm">
                Mileage: <b>{car.mileage}</b>
              </Text>

              <div style={{ flex: 1 }}></div>

              <Button 
                component="a" 
                href={car.link} 
                target="_blank" 
                fullWidth 
                mt="md" 
                radius="md"
                variant="filled"
                color="blue"
              >
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