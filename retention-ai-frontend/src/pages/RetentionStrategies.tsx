// RetentionStrategies page renders all users and lets you craft an email campaign.
// It loads churn users and fetches per-user recommendations from the backend.
// Fix: avoid showing placeholder "Failed to load explanation" by filtering it out
// when a backend explanation request fails and returns the fallback text.
import React, { useState, useEffect } from 'react';
import {
  Button,
  Card,
  Col,
  Form,
  Input,
  Row,
  Select,
  Switch,
  Typography,
  Alert,
  message,
  Spin,
  Tag,
  List
} from 'antd';
import {
  SearchOutlined,
  MailOutlined,
  SendOutlined,
  UserOutlined
} from '@ant-design/icons';
import { churnAPI, retentionAPI, UserExplanation } from '../services/api';

const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

// TypeScript interfaces
interface User {
  user_id: string;
  churn_probability: number;
  risk_level: string;
  recommendations?: string[];
  selectedRecommendations?: boolean[];
}

// API functions
const fetchChurnData = async (): Promise<User[]> => {
  try {
    const users = await churnAPI.getUsers();
    return users;
  } catch (error) {
    console.error('Error fetching churn data:', error);
    throw error;
  }
};

const fetchUserRecommendations = async (userId: string): Promise<string[]> => {
  try {
    const response = await churnAPI.getUserExplanation(userId);
    const recs = Array.isArray(response.data.recommendations)
      ? response.data.recommendations
      : [];
    // Only return real recommendations; no mock fallbacks
    return recs.filter((r) => r && !/^Failed to load explanation/i.test(r));
  } catch (error) {
    console.error('Error fetching user recommendations:', error);
    return [];
  }
};

const sendRetentionEmail = async (data: {
  email: string;
  subject: string;
  message: string;
  userIds: string[];
}): Promise<void> => {
  try {
    await retentionAPI.sendEmail(data);
    message.success('Email sent successfully!');
  } catch (error) {
    console.error('Error sending email:', error);
    message.error('Failed to send email. Please try again.');
    throw error;
  }
};

const RetentionStrategies: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState<boolean>(false);
  const [users, setUsers] = useState<User[]>([]);
  const [usersWithRecommendations, setUsersWithRecommendations] = useState<(User & { recommendations: string[] })[]>([]);
  const [error, setError] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');
    const [selectedUserIds, setSelectedUserIds] = useState<string[]>([]);
  const [sendingEmail, setSendingEmail] = useState<boolean>(false);
  const [loadingRecommendations, setLoadingRecommendations] = useState<boolean>(false);
  const [selectedRecommendations, setSelectedRecommendations] = useState<{[key: string]: number}>({});
  
  // Load users and their recommendations on component mount
  useEffect(() => {
    const loadUsers = async () => {
      try {
        setLoading(true);
        setError('');
        
        // Fetch churn data from API
        const churnData = await fetchChurnData();
        setUsers(churnData);
        
        // Load recommendations for ALL users (not just high-risk)
        setLoadingRecommendations(true);
        
        const usersWithRecs = await Promise.all(
          churnData.map(async (user) => {
            const recommendations = await fetchUserRecommendations(user.user_id);
            return {
              ...user,
              recommendations: recommendations.slice(0, 3) // Get top 3 recommendations
            };
          })
        );
        
        setUsersWithRecommendations(usersWithRecs);
        
      } catch (err) {
        console.error('Error loading users:', err);
        setError('Failed to load user data. Please try again.');
      } finally {
        setLoading(false);
        setLoadingRecommendations(false);
      }
    };
    
    loadUsers();
  }, []);
  
  // Toggle user selection
  const handleUserSelect = (userId: string) => {
    setSelectedUserIds(prev => {
      if (prev.includes(userId)) {
        // Remove user from selection
        const newSelections = {...selectedRecommendations};
        delete newSelections[userId];
        setSelectedRecommendations(newSelections);
        updateMessageBox();
        return prev.filter(id => id !== userId);
      } else {
        // Add user to selection with no recommendations selected by default
        return [...prev, userId];
      }
    });
  };

  // Select recommendation for a user (radio button behavior)
  const handleRecommendationSelect = (userId: string, index: number) => {
    if (!selectedUserIds.includes(userId)) return; // Only allow selection if user is selected
    
    setSelectedRecommendations(prev => {
      const newSelections = {
        ...prev,
        [userId]: index
      };
      
      // Update message box immediately with new selections
      setTimeout(() => {
        let recommendations = '';
        
        selectedUserIds.forEach(uid => {
          const user = usersWithRecommendations.find(u => u.user_id === uid);
          const selectedIndex = newSelections[uid];
          
          if (user?.recommendations && selectedIndex !== undefined && user.recommendations[selectedIndex]) {
            if (recommendations) recommendations += '\n\n';
            recommendations += user.recommendations[selectedIndex];
          }
        });
        
        let message = '';
        if (recommendations) {
          message = `Dear valued customer,\n\n${recommendations}\n\nBest regards,\nThe Retention Team`;
        }
        
        // Auto-populate subject if not already set
        const currentSubject = form.getFieldValue('subject');
        if (!currentSubject && recommendations) {
          form.setFieldsValue({ 
            message,
            subject: 'Personalized Recommendations to Enhance Your Experience'
          });
        } else {
          form.setFieldsValue({ message });
        }
      }, 10);
      
      return newSelections;
    });
  };

  // Update message box with selected recommendations
  const updateMessageBox = () => {
    let recommendations = '';
    
    selectedUserIds.forEach(userId => {
      const user = usersWithRecommendations.find(u => u.user_id === userId);
      const selectedIndex = selectedRecommendations[userId];
      
      if (user?.recommendations && selectedIndex !== undefined && user.recommendations[selectedIndex]) {
        if (recommendations) recommendations += '\n\n';
        recommendations += user.recommendations[selectedIndex];
      }
    });
    
    let message = '';
    if (recommendations) {
      message = `Dear valued customer,\n\n${recommendations}\n\nBest regards,\nThe Retention Team`;
    }
    
    form.setFieldsValue({ message });
  };

  // Get risk color
  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case 'high': return 'red';
      case 'medium': return 'orange';
      case 'low': return 'green';
      default: return 'gray';
    }
  };
  
  // Handle form submission
  const handleSendEmail = async (values: any) => {
    if (selectedUserIds.length === 0) {
      message.error('Please select at least one user');
      return;
    }
    
    // Check if at least one recommendation is selected per user
    const allUsersHaveSelections = selectedUserIds.every(userId => 
      selectedRecommendations[userId] !== undefined
    );
    
    if (!allUsersHaveSelections) {
      message.error('Please select one recommendation for each selected user');
      return;
    }
    
    try {
      setSendingEmail(true);
      
      // Use the message as is (it already contains selected recommendations)
      const messageWithRecommendations = values.message;
      
      await sendRetentionEmail({
        email: values.recipientEmail,
        subject: values.subject,
        message: messageWithRecommendations,
        userIds: selectedUserIds
      });
      
      // Reset form
      form.resetFields();
      setSelectedUserIds([]);
      setSelectedRecommendations({});
      
    } catch (error) {
      console.error('Error sending email:', error);
      // Error message is handled in sendRetentionEmail function
    } finally {
      setSendingEmail(false);
    }
  };
  
  // Filter users based on search term
  const filteredUsers = usersWithRecommendations.filter(user => 
    user.user_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div style={{ padding: '24px', backgroundColor: '#f5f5f5', minHeight: '100vh' }}>
      <Title level={2} style={{ marginBottom: '24px' }}>Retention Strategies</Title>
      
      <Row gutter={[24, 24]}>
        {/* All Users Panel */}
        <Col xs={24} md={10}>
          <Card 
            title="All Users" 
            extra={
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <Input
                  placeholder="Search users..."
                  prefix={<SearchOutlined />}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  style={{ width: 200 }}
                />
              </div>
            }
            style={{ height: '100%' }}
            bodyStyle={{ padding: '12px' }}
          >
            <Spin spinning={loading || loadingRecommendations}>
              {error ? (
                <Alert 
                  message={error} 
                  type="error" 
                  showIcon 
                />
              ) : (
                <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
                  <List
                    dataSource={filteredUsers}
                    renderItem={(user) => (
                      <List.Item
                        key={user.user_id}
                        style={{
                          padding: '12px',
                          margin: '8px 0',
                          backgroundColor: selectedUserIds.includes(user.user_id) ? '#e6f7ff' : '#fff',
                          border: '1px solid #d9d9d9',
                          borderRadius: '6px',
                          cursor: 'pointer'
                        }}
                        onClick={() => handleUserSelect(user.user_id)}
                      >
                        <div style={{ width: '100%' }}>
                          <div style={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            justifyContent: 'space-between',
                            marginBottom: '8px'
                          }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <UserOutlined />
                              <Text strong>User {user.user_id}</Text>
                            </div>
                            <Tag color={getRiskColor(user.risk_level)}>
                              {user.risk_level} ({user.churn_probability.toFixed(1)}%)
                            </Tag>
                          </div>
                          
                          {user.recommendations && user.recommendations.length > 0 && (
                            <div style={{ marginTop: '8px' }}>
                              <Text style={{ fontSize: '12px', color: '#666', fontWeight: 'bold' }}>Top Recommendations:</Text>
                              <ul style={{ margin: '4px 0', paddingLeft: '0' }}>
                                {user.recommendations.map((rec, index) => (
                                  <li 
                                    key={index} 
                                    style={{ 
                                      display: 'flex', 
                                      alignItems: 'flex-start', 
                                      marginBottom: '4px',
                                      padding: '2px 0',
                                      cursor: 'pointer'
                                    }}
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleRecommendationSelect(user.user_id, index);
                                    }}
                                  >
                                    <input
                                      type="radio"
                                      name={`recommendations-${user.user_id}`}
                                      checked={selectedRecommendations[user.user_id] === index}
                                      disabled={!selectedUserIds.includes(user.user_id)}
                                      onChange={(e) => {
                                        e.stopPropagation();
                                        handleRecommendationSelect(user.user_id, index);
                                      }}
                                      style={{
                                        marginRight: '8px',
                                        marginTop: '2px',
                                        cursor: selectedUserIds.includes(user.user_id) ? 'pointer' : 'not-allowed'
                                      }}
                                    />
                                    <span style={{ 
                                      fontSize: '11px', 
                                      color: selectedUserIds.includes(user.user_id) ? '#666' : '#ccc',
                                      fontWeight: selectedRecommendations[user.user_id] === index ? 'bold' : 'normal',
                                      opacity: selectedUserIds.includes(user.user_id) ? 1 : 0.5
                                    }}>
                                      {rec.length > 50 ? rec.substring(0, 50) + '...' : rec}
                                    </span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </List.Item>
                    )}
                  />
                  
                  {filteredUsers.length === 0 && !loading && (
                    <div style={{ textAlign: 'center', padding: '20px', color: '#666' }}>
                      {searchTerm ? 'No users found matching your search.' : 'No users found.'}
                    </div>
                  )}
                </div>
              )}
            </Spin>
          </Card>
        </Col>
        
        {/* Create Retention Campaign Panel */}
        <Col xs={24} md={14}>
          <Card 
            title="Create Retention Campaign" 
            style={{ height: '100%' }}
            bodyStyle={{ padding: '16px' }}
          >
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSendEmail}
            >
              <Form.Item label="Action Type">
                <Select 
                  defaultValue="email" 
                  style={{ width: '100%' }}
                  disabled
                >
                  <Option value="email">
                    <MailOutlined style={{ marginRight: '8px' }} />
                    Send Email
                  </Option>
                </Select>
              </Form.Item>
              
              <Form.Item
                label="Recipient Email"
                name="recipientEmail"
                rules={[
                  { required: true, message: 'Please enter recipient email' },
                  { type: 'email', message: 'Please enter a valid email' }
                ]}
              >
                <Input 
                  placeholder="Enter recipient email "
                  prefix={<MailOutlined />}
                />
              </Form.Item>
              
              <Form.Item 
                label="Subject" 
                name="subject"
                rules={[{ required: true, message: 'Please enter email subject' }]}
              >
                <Input placeholder="Enter email subject" />
              </Form.Item>
              
              <Form.Item 
                label="Message" 
                name="message"
                rules={[{ required: true, message: 'Please enter your message' }]}
              >
                <TextArea 
                  rows={6} 
                  placeholder="Enter your message here..."
                />
              </Form.Item>
              
              <Form.Item>
                <Text style={{ fontSize: '12px', color: '#666' }}>
                  Selected Users: {selectedUserIds.length}
                </Text>
              </Form.Item>
              
              <Form.Item>
                <Button 
                  type="primary" 
                  htmlType="submit"
                  loading={sendingEmail}
                  icon={<SendOutlined />}
                  size="large"
                  style={{ width: '100%' }}
                  disabled={selectedUserIds.length === 0}
                >
                  {sendingEmail ? 'SENDING...' : 'SEND EMAIL'}
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default RetentionStrategies;
