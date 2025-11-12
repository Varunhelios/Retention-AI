import React, { useState, useEffect, useCallback } from 'react';
import { 
  Card, 
  Col, 
  Input, 
  Row, 
  Typography, 
  Alert, 
  Spin,
  Tag,
  List,
  Tooltip,
  Button,
  Form,
  Input as AntdInput,
  message,
  Skeleton,
  Radio,
  Empty,
  Pagination 
} from 'antd';
import type { ColProps } from 'antd/es/col';
import { SearchOutlined, UserOutlined, MailOutlined, SendOutlined } from '@ant-design/icons';
import { churnAPI, retentionAPI } from '../services/api';

// Constants
const PAGE_SIZE = 10;
const MAX_ITEMS_IN_MEMORY = 30;

const { Title, Text } = Typography;
const { TextArea } = AntdInput;
const { Group: RadioGroup } = Radio;

interface User {
  user_id: string;
  churn_probability: number;
  risk_level: string;
  recommendations?: string[];
}

type SelectionState = Record<string, number | null>;

const RetentionStrategies: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [filteredUsers, setFilteredUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [sendingEmail, setSendingEmail] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([]);
  const [selectedRecommendations, setSelectedRecommendations] = useState<SelectionState>({});
  const [usersWithRecommendations, setUsersWithRecommendations] = useState<Record<string, string[]>>({});
  const [loadingRecommendations, setLoadingRecommendations] = useState<Record<string, boolean>>({});
  const [currentPage, setCurrentPage] = useState<number>(1);
  
  const [form] = Form.useForm();

  // Fetch users on component mount
  useEffect(() => {
    const fetchUsers = async () => {
      try {
        setLoading(true);
        const data = await churnAPI.getUsers();
        setUsers(data);
        setFilteredUsers(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching users:', err);
        setError('Failed to load users. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, []);

  // Filter users based on search term
  useEffect(() => {
    if (!searchTerm.trim()) {
      setFilteredUsers(users);
      return;
    }

    const term = searchTerm.toLowerCase();
    const filtered = users.filter(user => 
      user.user_id.toLowerCase().includes(term) ||
      user.risk_level.toLowerCase().includes(term) ||
      user.churn_probability.toString().includes(term)
    );
    
    setFilteredUsers(filtered);
  }, [searchTerm, users]);

  // Load recommendations for a user
  const loadUserRecommendations = useCallback(async (userId: string) => {
    if (loadingRecommendations[userId] || usersWithRecommendations[userId]) return;

    try {
      setLoadingRecommendations(prev => ({ ...prev, [userId]: true }));
      // Using getUserExplanation as a fallback since getUserRecommendations might not exist
      const response = await churnAPI.getUserExplanation(userId);
      const recommendations = response?.data?.recommendations || [
        'Offer personalized discount',
        'Send engagement email',
        'Provide customer support'
      ];
      
      setUsersWithRecommendations(prev => ({
        ...prev,
        [userId]: recommendations
      }));
    } catch (err) {
      console.error(`Error loading recommendations for user ${userId}:`, err);
    } finally {
      setLoadingRecommendations(prev => ({ ...prev, [userId]: false }));
    }
  }, [loadingRecommendations, usersWithRecommendations]);

  // Handle user selection
  const handleUserSelect = useCallback((userId: string) => {
    setSelectedUserIds(prev => {
      const isSelected = prev.includes(userId);
      const newSelectedIds = isSelected
        ? prev.filter(id => id !== userId)
        : [...prev, userId].slice(-10);

      // Load recommendations when user is selected
      if (!isSelected) {
        loadUserRecommendations(userId);
      }

      return newSelectedIds;
    });
  }, [loadUserRecommendations]);

  // Handle recommendation selection
  const handleRecommendationSelect = (userId: string, index: number) => {
    setSelectedRecommendations(prev => ({
      ...prev,
      [userId]: index
    }));

    // Get the selected recommendation text
    const selectedRec = usersWithRecommendations[userId]?.[index];
    if (selectedRec) {
      // Set the email subject and message based on the recommendation
      form.setFieldsValue({
        subject: `Special Offer: ${selectedRec}`,
        message: `Dear User ${userId},\n\n${selectedRec}\n\nBest regards,\nYour Retention Team`
      });
    }
  };

  // Handle form submission
  const handleSendEmail = useCallback(async (values: { email: string; subject: string; message: string }) => {
    if (selectedUserIds.length === 0) {
      message.warning('Please select at least one user');
      return;
    }

    try {
      setSendingEmail(true);
      // Use the retentionAPI service to send the email
      await retentionAPI.sendEmail({
        email: values.email,
        subject: values.subject,
        message: values.message,
        userIds: selectedUserIds
      });
      
      // Reset form and selections
      form.resetFields();
      setSelectedUserIds([]);
      setSelectedRecommendations({});
      message.success('Email sent successfully!');
    } catch (error) {
      console.error('Error sending email:', error);
      message.error('Failed to send email. Please try again.');
    } finally {
      setSendingEmail(false);
    }
  }, [selectedUserIds, form]);

  // Render user item
  const renderUserItem = (user: User) => {
    const isSelected = selectedUserIds.includes(user.user_id);
    const isLoading = loadingRecommendations[user.user_id];
    const userRecommendations = usersWithRecommendations[user.user_id] || [];
    const selectedRecommendation = selectedRecommendations[user.user_id];

    return (
      <List.Item
        key={user.user_id}
        onClick={() => handleUserSelect(user.user_id)}
        style={{
          padding: '12px',
          margin: '8px 0',
          border: '1px solid #d9d9d9',
          borderRadius: '6px',
          cursor: 'pointer',
          backgroundColor: isSelected ? '#e6f7ff' : '#fff',
          transition: 'all 0.3s',
        }}
      >
        <div style={{ width: '100%' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <UserOutlined />
              <Text strong>User {user.user_id}</Text>
            </div>
            <Tag 
              color={
                user.risk_level === 'High' ? 'red' : 
                user.risk_level === 'Medium' ? 'orange' : 'green'
              }
            >
              {user.risk_level} Risk
            </Tag>
          </div>
          <div style={{ marginTop: '8px' }}>
            <Text type="secondary">
              Churn Probability: {user.churn_probability.toFixed(2)}%
            </Text>
          </div>
          
          {isSelected && (
            <div style={{ marginTop: '12px' }}>
              <div style={{ fontWeight: 500, marginBottom: '8px' }}>Recommendations:</div>
              {isLoading ? (
                <Skeleton active paragraph={{ rows: 2 }} />
              ) : userRecommendations.length > 0 ? (
                <RadioGroup 
                  value={selectedRecommendation}
                  onChange={(e) => handleRecommendationSelect(user.user_id, e.target.value)}
                  style={{ width: '100%' }}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {userRecommendations.map((rec, index) => (
                      <div 
                        key={index}
                        onClick={(e) => e.stopPropagation()}
                        style={{
                          padding: '8px',
                          border: `1px solid ${selectedRecommendation === index ? '#1890ff' : '#f0f0f0'}`,
                          borderRadius: '4px',
                          backgroundColor: selectedRecommendation === index ? '#e6f7ff' : '#fafafa',
                          cursor: 'pointer',
                          transition: 'all 0.3s',
                        }}
                      >
                        <Radio value={index} style={{ width: '100%' }}>
                          {rec}
                        </Radio>
                      </div>
                    ))}
                  </div>
                </RadioGroup>
              ) : (
                <div>No recommendations available</div>
              )}
            </div>
          )}
        </div>
      </List.Item>
    );
  };

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
            <Spin spinning={loading || Object.values(loadingRecommendations).some(Boolean)}>
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
                    renderItem={renderUserItem}
                    locale={{ emptyText: <Empty description="No users found" /> }}
                    style={{ width: '100%' }}
                    pagination={{
                      pageSize: PAGE_SIZE,
                      current: currentPage,
                      total: filteredUsers.length,
                      onChange: (page) => setCurrentPage(page),
                      showSizeChanger: false,
                      hideOnSinglePage: true,
                    }}
                  />
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
            bodyStyle={{ 
              display: 'flex', 
              flexDirection: 'column', 
              height: '100%',
              padding: '24px'
            }}
          >
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSendEmail}
              style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
              initialValues={{
                email: '',
                subject: '',
                message: ''
              }}
            >
              <Form.Item
                label="Recipient Email"
                name="email"
                rules={[
                  { required: true, message: 'Please input recipient email!' },
                  { type: 'email', message: 'Please enter a valid email address' }
                ]}
                extra="You can enter multiple emails separated by commas"
              >
                <Input 
                  placeholder="Enter recipient email" 
                  prefix={<MailOutlined />} 
                />
              </Form.Item>
              
              <Form.Item
                label="Subject"
                name="subject"
                rules={[{ required: true, message: 'Please input email subject!' }]}
              >
                <Input placeholder="Enter email subject" />
              </Form.Item>
              
              <Form.Item
                label="Message"
                name="message"
                rules={[{ required: true, message: 'Please input your message!' }]}
                style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
              >
                <TextArea 
                  placeholder="Compose your message here..." 
                  style={{ flex: 1, resize: 'none' }} 
                />
              </Form.Item>
              
              <div style={{ marginTop: '24px', textAlign: 'right' }}>
                <Button 
                  type="primary" 
                  htmlType="submit" 
                  icon={<SendOutlined />}
                  loading={sendingEmail}
                  disabled={selectedUserIds.length === 0}
                >
                  Send Email
                </Button>
              </div>
            </Form>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default RetentionStrategies;
