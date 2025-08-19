import React, { useState, useEffect } from 'react';
import { Row, Col, Button, message, Tag, Input, Spin, Card, List, Typography, Select, Space } from 'antd';
import { SearchOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { churnAPI, User, UserExplanation as CustomerExplanation } from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;

// Type for the API response item
interface Factor {
  feature: string;
  value: string | number;
  impact: number;
  description?: string;
  explanation?: string;
}

// Type for the API response
interface ApiResponse<T> {
  data: T;
  status?: number;
  statusText?: string;
}

interface LoadingState {
  userExplanation: boolean;
  predictions: boolean;
}

const ExplainableAI: React.FC = () => {
  const [selectedUserId, setSelectedUserId] = useState<string>('1001');
  const [loading, setLoading] = useState<LoadingState>({
    userExplanation: false,
    predictions: false
  });
  const [userExplanation, setUserExplanation] = useState<CustomerExplanation | null>(null);
  const [availableUsers, setAvailableUsers] = useState<User[]>([]);
  
  // Load available users on component mount
  useEffect(() => {
    const loadUserData = async () => {
      try {
        updateLoading('predictions', true);
        
        // Try to load users from the main endpoint first
        try {
          const usersResponse = await churnAPI.getUsers();
          setAvailableUsers(usersResponse);
          
          // If we have users but none selected, select the first one
          if (usersResponse.length > 0 && !selectedUserId) {
            setSelectedUserId(usersResponse[0].user_id);
          }
        } catch (usersError) {
          console.error('Error loading users:', usersError);
          
          // Fallback to churn predictions if users endpoint fails
          try {
            const response = await churnAPI.getChurnPredictions();
            const predictions = response?.data?.data || [];
            if (Array.isArray(predictions) && predictions.length > 0) {
              const users = predictions.map(item => ({
                user_id: String(item.userid),
                churn_probability: item['churn_probability (%)'] || 0,
                risk_level: item.churn_risk || 'Medium'
              }));
              
              setAvailableUsers(users);
              if (!selectedUserId && users.length > 0) {
                setSelectedUserId(users[0].user_id);
              }
            }
          } catch (fallbackError) {
            console.error('Error loading fallback user data:', fallbackError);
            message.error('Failed to load user data. Please try again later.');
          }
        }
      } catch (error) {
        console.error('Error in user data loading:', error);
        message.error('Failed to load user data');
      } finally {
        updateLoading('predictions', false);
      }
    };

    loadUserData();
  }, [selectedUserId]);
  
  // Helper function to safely update loading state
  const updateLoading = (key: keyof LoadingState, value: boolean) => {
    setLoading((prev) => ({ ...prev, [key]: value }));
  };

  const handleGetExplanation = async () => {
    if (!selectedUserId) {
      message.warning('Please select a user');
      return;
    }
    
    try {
      updateLoading('userExplanation', true);
      // Clear previous explanation while loading
      setUserExplanation(null);
      
      // Add a small delay to show loading state
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const response = await churnAPI.getUserExplanation(selectedUserId);
      
      if (!response || !response.data) {
        throw new Error('Invalid response from server');
      }
      
      setUserExplanation(response.data);
      
    } catch (error) {
      console.error('Error fetching user explanation:', error);
      message.error('Failed to fetch user explanation. Please try again.');
      // Set a default explanation with error state
      // Create a valid UserExplanation object for error state
      const errorExplanation: CustomerExplanation = {
        user_id: selectedUserId,
        churn_probability: 0,
        risk_level: 'error',
        top_features: [{
          feature: 'Error',
          value: 0, // Changed to number to match type
          shap_value: 0,
          model: 'Error'
        }],
        recommendations: [
          'Please check if the backend server is running',
          'Verify the user ID exists in the system',
          'Try refreshing the page or selecting a different user'
        ]
      };
      setUserExplanation(errorExplanation);
    } finally {
      updateLoading('userExplanation', false);
    }
  };

  const handleUserSelect = (userId: string) => {
    setSelectedUserId(userId);
    handleGetExplanation();
  };

  // Load explanation when selectedUserId changes
  useEffect(() => {
    if (selectedUserId) {
      handleGetExplanation();
    }
  }, [selectedUserId]); // This effect runs when selectedUserId changes

  return (
    <div style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}>
      <Title level={2} style={{ marginBottom: '24px' }}>Explainable AI</Title>
      <Text type="secondary" style={{ display: 'block', marginBottom: '24px' }}>
        Understand model predictions and get personalized recommendations to reduce churn risk.
      </Text>
      
      <Row gutter={[24, 24]}>
        {/* Left Column - User Selection and Risk Factors */}
        <Col span={12}>
          {/* User Selection */}
          <Card title="Search User" style={{ marginBottom: 16 }}>
            <Space.Compact style={{ width: '100%' }}>
              <Select
                showSearch
                style={{ width: '100%' }}
                placeholder="Search user by ID"
                optionFilterProp="children"
                value={selectedUserId}
                onChange={(value: string) => setSelectedUserId(value)}
                onSearch={(value) => setSelectedUserId(value)}
                filterOption={(input, option) =>
                  (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                }
                options={availableUsers.map(user => ({
                  value: user.user_id,
                  label: `${user.user_id} (${user.risk_level})`,
                }))}
              />
              <Button 
                type="primary" 
                icon={<SearchOutlined />} 
                onClick={handleGetExplanation}
                loading={loading.userExplanation}
              >
                Get Explanation
              </Button>
            </Space.Compact>
          </Card>

          {/* Key Risk Factors */}
          <Card title="⚠️ Key Risk Factors" style={{ marginBottom: 16 }}>
            <Spin spinning={loading.userExplanation}>
              {userExplanation ? (
                <List
                  dataSource={userExplanation.top_features.slice(0, 5)}
                  renderItem={(factor: any, index: number) => (
                    <List.Item style={{ 
                      padding: '12px 0',
                      borderBottom: index < 4 ? '1px solid #f0f0f0' : 'none'
                    }}>
                      <div style={{ width: '100%' }}>
                        <div style={{ 
                          display: 'flex', 
                          justifyContent: 'space-between', 
                          alignItems: 'flex-start',
                          marginBottom: 8 
                        }}>
                          <div style={{ flex: 1 }}>
                            <Text strong style={{ fontSize: 14, color: '#1890ff' }}>
                              {factor.feature}
                            </Text>
                            <div style={{ fontSize: 12, color: '#666', marginTop: 2 }}>
                              {factor.description || 'Business impact factor'}
                            </div>
                          </div>
                          <div style={{ textAlign: 'right', marginLeft: 16 }}>
                            <Tag color={factor.shap_value > 0 ? 'red' : 'green'} style={{ margin: 0 }}>
                              {factor.shap_value > 0 ? '📈 Risk' : '📉 Safe'}
                            </Tag>
                          </div>
                        </div>
                        
                        {/* Business-friendly explanation */}
                        <div style={{ 
                          backgroundColor: '#f8f9fa', 
                          padding: '8px 12px', 
                          borderRadius: 6,
                          fontSize: 13,
                          lineHeight: 1.4
                        }}>
                          <Text>{factor.explanation || `Value: ${factor.value} - Impact: ${Math.abs(factor.shap_value).toFixed(3)}`}</Text>
                        </div>
                      </div>
                    </List.Item>
                  )}
                />
              ) : (
                <Text type="secondary">Select a user to view risk factors</Text>
              )}
            </Spin>
          </Card>

          {/* Recommendations */}
          <Card title="💡 Recommended Actions" style={{ marginBottom: 16 }}>
            <Spin spinning={loading.userExplanation}>
              {userExplanation && userExplanation.recommendations ? (
                <List
                  dataSource={userExplanation.recommendations}
                  renderItem={(recommendation: string, index: number) => (
                    <List.Item style={{ 
                      padding: '8px 0',
                      borderBottom: index < userExplanation.recommendations.length - 1 ? '1px solid #f0f0f0' : 'none'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                        <div style={{ 
                          backgroundColor: '#1890ff', 
                          color: 'white', 
                          borderRadius: '50%', 
                          width: 20, 
                          height: 20, 
                          display: 'flex', 
                          alignItems: 'center', 
                          justifyContent: 'center', 
                          fontSize: 12, 
                          marginRight: 12,
                          flexShrink: 0
                        }}>
                          {index + 1}
                        </div>
                        <Text style={{ flex: 1, lineHeight: 1.5 }}>{recommendation}</Text>
                      </div>
                    </List.Item>
                  )}
                />
              ) : (
                <Text type="secondary">Select a user to view recommendations</Text>
              )}
            </Spin>
          </Card>
        </Col>

        {/* Right Column - Charts and User Summary */}
        <Col span={12}>
          {/* Top Influencing Factors Chart */}
          <Card title="📊 Top Influencing Factors" style={{ marginBottom: 16 }}>
            <Spin spinning={loading.userExplanation}>
              {userExplanation ? (
                <div>
                  <div style={{ textAlign: 'center', marginBottom: 16 }}>
                    <img 
                      src={`http://localhost:8000/api/user/${selectedUserId}/chart`}
                      alt={`SHAP chart for user ${selectedUserId}`}
                      style={{ maxWidth: '100%', height: 'auto', borderRadius: 6 }}
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                  <Text type="secondary">Select a user to view influencing factors chart</Text>
                </div>
              )}
            </Spin>
          </Card>

          {/* User Summary */}
          <Card title="👤 User Summary" style={{ marginBottom: 16 }}>
            <Spin spinning={loading.userExplanation}>
              {userExplanation ? (
                <div>
                  <div style={{ marginBottom: 16 }}>
                    <Text strong style={{ fontSize: 16 }}>User ID</Text>
                    <div style={{ fontSize: 24, fontWeight: 'bold', marginTop: 4 }}>
                      {userExplanation.user_id}
                    </div>
                    <div style={{ marginTop: 8, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      <Tag 
                        color={userExplanation.churn_probability > 70 ? 'red' : userExplanation.churn_probability > 40 ? 'orange' : 'green'}
                        style={{ fontSize: 14, padding: '4px 12px' }}
                      >
                        {userExplanation.churn_probability.toFixed(1)}% Churn Risk
                      </Tag>
                      <Tag 
                        color={userExplanation.risk_level === 'High' ? 'red' : userExplanation.risk_level === 'Medium' ? 'orange' : 'green'}
                        style={{ fontSize: 14, padding: '4px 12px' }}
                      >
                        {userExplanation.risk_level} Risk
                      </Tag>
                    </div>
                  </div>
                  
                  <div style={{ marginTop: 16 }}>
                    <Text strong>🎯 Key Insights</Text>
                    <div style={{ marginTop: 8 }}>
                      {userExplanation.top_features.slice(0, 3).map((factor: any, index: number) => (
                        <div key={index} style={{ 
                          padding: '8px 0',
                          borderBottom: index < 2 ? '1px solid #f0f0f0' : 'none'
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
                            <Text strong style={{ fontSize: 13 }}>{factor.feature}</Text>
                            <div style={{ marginLeft: 'auto' }}>
                              {factor.shap_value > 0 ? (
                                <ArrowUpOutlined style={{ color: '#ff4d4f', fontSize: 12 }} />
                              ) : (
                                <ArrowDownOutlined style={{ color: '#52c41a', fontSize: 12 }} />
                              )}
                            </div>
                          </div>
                          <div style={{ fontSize: 11, color: '#666', lineHeight: 1.3 }}>
                            {factor.explanation ? 
                              factor.explanation.substring(0, 80) + (factor.explanation.length > 80 ? '...' : '') :
                              `${factor.shap_value > 0 ? 'Increases' : 'Reduces'} churn risk`
                            }
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  {/* Model Information */}
                  <div style={{ marginTop: 16, padding: '8px 12px', backgroundColor: '#f8f9fa', borderRadius: 6 }}>
                    <Text style={{ fontSize: 12, color: '#666' }}>
                      📊 Analysis based on {userExplanation.model_b_used ? 'behavioral + sentiment data' : 'behavioral data only'}
                    </Text>
                  </div>
                </div>
              ) : (
                <Text type="secondary">Select a user to view summary</Text>
              )}
            </Spin>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default ExplainableAI;
