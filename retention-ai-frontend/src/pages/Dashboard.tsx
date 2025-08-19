import React, { useState, useEffect } from 'react';
import { Row, Col, Statistic, Card, Typography, Spin, Tag } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, UserOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import GridItem from '../components/ui/GridItem';
import { dashboardAPI, churnAPI } from '../services/api';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  LineChart,
  Line,
  ResponsiveContainer
} from 'recharts';

const { Title, Text } = Typography;

interface DashboardStats {
  total_users: number;
  churn_rate: number;
  retention_rate: number;
  recent_activity: Array<{userid: string; risk: string}>;
}

interface ChartData {
  riskDistribution: Array<{name: string; value: number; color: string}>;
  churnProbabilityDistribution: Array<{range: string; count: number}>;
  modelAccuracyMetrics: Array<{metric: string; value: number; color: string}>;
}

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<DashboardStats>({
    total_users: 0,
    churn_rate: 0,
    retention_rate: 0,
    recent_activity: []
  });
  
  const [chartData, setChartData] = useState<ChartData>({
    riskDistribution: [],
    churnProbabilityDistribution: [],
    modelAccuracyMetrics: []
  });

  // Fetch dashboard data from the API
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch basic stats
        const response = await dashboardAPI.getStats();
        setStats(response.data);
        
        // Fetch users for chart data
        const usersResponse = await churnAPI.getUsers();
        const users = usersResponse;
        
        // Process data for charts - using churn_probability for consistency
        const probabilityBasedCounts = { High: 0, Medium: 0, Low: 0 };
        users.forEach(user => {
          const prob = user.churn_probability;
          if (prob >= 70) {
            probabilityBasedCounts.High++;
          } else if (prob >= 30) {
            probabilityBasedCounts.Medium++;
          } else {
            probabilityBasedCounts.Low++;
          }
        });
        
        const riskDistribution = [
          { name: 'High Risk (70-100%)', value: probabilityBasedCounts.High, color: '#ff4d4f' },
          { name: 'Medium Risk (30-70%)', value: probabilityBasedCounts.Medium, color: '#faad14' },
          { name: 'Low Risk (0-30%)', value: probabilityBasedCounts.Low, color: '#52c41a' }
        ];
        
        // Generate churn probability distribution from real user data
        const probabilityRanges = {
          'Low (0-30%)': 0,
          'Medium (30-70%)': 0,
          'High (70-100%)': 0
        };
        
        users.forEach(user => {
          const prob = user.churn_probability;
          if (prob < 30) {
            probabilityRanges['Low (0-30%)']++;
          } else if (prob < 70) {
            probabilityRanges['Medium (30-70%)']++;
          } else {
            probabilityRanges['High (70-100%)']++;
          }
        });
        
        const churnProbabilityDistribution = Object.entries(probabilityRanges).map(([range, count]) => ({
          range,
          count
        }));
        
        // Generate model accuracy metrics from real data
        const totalUsers = users.length;
        const highRiskUsers = probabilityBasedCounts.High;
        const mediumRiskUsers = probabilityBasedCounts.Medium;
        const lowRiskUsers = probabilityBasedCounts.Low;
        
        const businessMetrics = [
          {
            metric: 'High Risk Users',
            value: totalUsers > 0 ? Math.round((highRiskUsers / totalUsers) * 100) : 0,
            color: '#ff4d4f'
          },
          {
            metric: 'At-Risk Users',
            value: totalUsers > 0 ? Math.round(((highRiskUsers + mediumRiskUsers) / totalUsers) * 100) : 0,
            color: '#faad14'
          },
          {
            metric: 'Retention Rate',
            value: Math.round(response.data.retention_rate || 0),
            color: '#52c41a'
          }
        ];
        
        setChartData({
          riskDistribution,
          churnProbabilityDistribution,
          modelAccuracyMetrics: businessMetrics
        });
        
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: '40px 20px' }}>
        <ExclamationCircleOutlined style={{ fontSize: '48px', color: '#ff4d4f', marginBottom: '16px' }} />
        <Title level={4}>{error}</Title>
        <Text type="secondary">Please check your connection and try again.</Text>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <Title level={2} style={{ margin: 0 }}>Dashboard Overview</Title>
        <Text type="secondary">Last updated: {new Date().toLocaleString()}</Text>
      </div>
      
      <Spin spinning={loading}>
        <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
          <Col xs={24} sm={12} lg={8}>
            <Card>
              <Statistic
                title="Total Users"
                value={stats.total_users}
                prefix={<UserOutlined />}
                loading={loading}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={8}>
            <Card>
              <Statistic
                title="Churn Rate"
                value={stats.churn_rate}
                precision={2}
                valueStyle={{ color: '#cf1322' }}
                prefix={<ArrowUpOutlined />}
                suffix="%"
                loading={loading}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={8}>
            <Card>
              <Statistic
                title="Retention Rate"
                value={stats.retention_rate}
                precision={2}
                valueStyle={{ color: '#3f8600' }}
                prefix={<ArrowDownOutlined />}
                suffix="%"
                loading={loading}
              />
            </Card>
          </Col>
        </Row>

        {/* Charts Section */}
        <Row gutter={[16, 16]} style={{ marginTop: '24px' }}>
          {/* Risk Distribution Pie Chart */}
          <Col xs={24} lg={12}>
            <Card title="Risk Distribution" style={{ height: '400px' }}>
              {loading ? (
                <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Spin size="large" />
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={chartData.riskDistribution}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {chartData.riskDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </Card>
          </Col>

          {/* Churn Probability Distribution Bar Chart */}
          <Col xs={24} lg={12}>
            <Card title="Churn Probability Distribution" style={{ height: '400px' }}>
              {loading ? (
                <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Spin size="large" />
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={chartData.churnProbabilityDistribution}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="range" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="count" fill="#1890ff" name="Number of Users" />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </Card>
          </Col>

          {/* Business Metrics Bar Chart */}
          <Col xs={24} lg={24}>
            <Card title="Business Risk Metrics" style={{ height: '400px' }}>
              {loading ? (
                <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Spin size="large" />
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={chartData.modelAccuracyMetrics}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="metric" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip formatter={(value) => [`${value}%`, 'Value']} />
                    <Legend />
                    <Bar dataKey="value" name="Percentage">
                      {chartData.modelAccuracyMetrics.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </Card>
          </Col>


        </Row>
      </Spin>
    </div>
  );
};

export default Dashboard;
