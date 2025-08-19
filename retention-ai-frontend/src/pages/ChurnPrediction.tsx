import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Table, Tag, Input, Button, Select, Form, message, Typography } from 'antd';
import { SearchOutlined, FilterOutlined, DownloadOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { churnAPI } from '../services/api';

const { Title } = Typography;
const { Option } = Select;

// Interface for churn prediction data
interface ChurnPrediction {
  key: string;
  customerId: string;
  risk: string;
  probability: string;
}

interface ApiResponseItem {
  userid: string;
  customerId?: string;
  churn_risk: string;
  'churn_probability (%)': number;
}

interface ApiResponse {
  data: {
    data: ApiResponseItem[];
  };
}

const columns = [
  {
    title: 'S.No',
    key: 'sno',
    width: '10%',
    render: (_: any, __: any, index: number) => index + 1,
  },
  {
    title: 'User ID',
    dataIndex: 'customerId',
    key: 'customerId',
    width: '30%',
    render: (text: string) => (
      <div style={{ 
        whiteSpace: 'normal',
        wordWrap: 'break-word',
        padding: '8px 0'
      }}>
        {text}
      </div>
    ),
  },
  {
    title: 'Churn Risk',
    dataIndex: 'risk',
    key: 'risk',
    width: '20%',
    render: (risk: string) => {
      const color = risk === 'High' ? 'red' : risk === 'Medium' ? 'orange' : 'green';
      return (
        <Tag color={color} key={risk}>
          {risk.toUpperCase()}
        </Tag>
      );
    },
    filters: [
      { text: 'High', value: 'High' },
      { text: 'Medium', value: 'Medium' },
      { text: 'Low', value: 'Low' },
    ],
    onFilter: (value: any, record: any) => record.risk === value,
    sorter: (a: any, b: any) => a.risk.localeCompare(b.risk),
  },
  {
    title: 'Probability',
    dataIndex: 'probability',
    key: 'probability',
    width: '20%',
    sorter: (a: any, b: any) => {
      const aValue = typeof a.probability === 'number' ? a.probability : parseFloat(a.probability) || 0;
      const bValue = typeof b.probability === 'number' ? b.probability : parseFloat(b.probability) || 0;
      return aValue - bValue;
    },
    render: (text: string | number) => {
      try {
        // Handle null/undefined/empty cases
        if (text === null || text === undefined || text === '') {
          return 'N/A';
        }
        
        // Convert to number if it's a string
        let num: number;
        if (typeof text === 'string') {
          // Remove any non-numeric characters except decimal point and negative sign
          const cleaned = text.toString().replace(/[^0-9.-]/g, '');
          num = parseFloat(cleaned);
        } else {
          num = text;
        }
        
        // If it's a valid number, format it as a percentage
        if (!isNaN(num)) {
          // Ensure the number is between 0 and 100
          const percentage = Math.min(100, Math.max(0, num));
          return `${percentage.toFixed(1)}%`;
        }
        
        return 'N/A';
      } catch (error) {
        console.error('Error formatting probability:', error, 'Value:', text);
        return 'N/A';
      }
    },
  },
];

const ChurnPrediction: React.FC = () => {
  const [searchText, setSearchText] = useState('');
  const [loading, setLoading] = useState(true);
  const [predictions, setPredictions] = useState<ChurnPrediction[]>([]);
  const [filteredData, setFilteredData] = useState<ChurnPrediction[]>([]);
  const [form] = Form.useForm();

  // Load churn predictions from API
  useEffect(() => {
    const loadPredictions = async () => {
      try {
        setLoading(true);
        const response = await churnAPI.getChurnPredictions() as unknown as ApiResponse;
        
        // Transform the API response to match our table format
        const formattedData: ChurnPrediction[] = response.data.data.map((item) => ({
          key: item.userid,
          customerId: item.customerId || item.userid,
          risk: item.churn_risk,
          probability: item['churn_probability (%)'].toString(),
        }));
        
        console.log('Formatted data:', formattedData); // Debug log
        setPredictions(formattedData);
        setFilteredData(formattedData);
      } catch (error) {
        console.error('Error loading churn predictions:', error);
        message.error('Failed to load churn prediction data');
      } finally {
        setLoading(false);
      }
    };

    loadPredictions();
  }, []);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchText(value);
    
    if (!value) {
      setFilteredData(predictions);
      return;
    }
    
    const filtered = predictions.filter(
      (item) => item.customerId?.toLowerCase().includes(value.toLowerCase())
    );
    
    setFilteredData(filtered);
  };

  const handleFilter = (values: any) => {
    // Apply additional filters to the data
    let result = [...predictions];
    
    if (values.risk) {
      result = result.filter(item => item.risk === values.risk);
    }
    
    setFilteredData(result);
  };

  const handleExport = () => {
    // Implement export functionality
    console.log('Exporting data...');
    message.info('Export functionality will be implemented soon');
  };

  return (
    <div className="churn-prediction" style={{ padding: 0, margin: 0, height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '24px 24px 0' }}>
        <Title level={2} style={{ margin: 0, paddingBottom: '16px' }}>Churn Prediction</Title>
      </div>
      <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
        <Col xs={24} md={12}>
          <Input
            placeholder="Search by User ID or Risk Level..."
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={handleSearch}
            style={{ width: '100%' }}
            allowClear
          />
        </Col>
        <Col xs={24} md={12} style={{ textAlign: 'right' }}>
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            onClick={handleExport}
          >
            Export
          </Button>
        </Col>
      </Row>

      <div style={{ 
        flex: 1,
        width: '100%',
        display: 'flex', 
        flexDirection: 'column',
        overflow: 'hidden',
        margin: 0,
        padding: '0 24px 24px'
      }}>
        <Card style={{ 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column',
          overflow: 'hidden'
        }} bodyStyle={{ 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column',
          padding: 0 
        }}>
          <div style={{ flex: 1, overflow: 'auto' }}>
            <Table
              columns={columns}
              dataSource={filteredData}
              loading={loading}
              pagination={false}
              scroll={{ y: 'calc(100vh - 300px)' }}
              style={{ width: '100%', tableLayout: 'fixed' }}
              rowKey="key"
              components={{
                body: {
                  row: (props: { children: React.ReactNode; [key: string]: any }) => {
                    const { children, ...restProps } = props;
                    return (
                      <tr {...restProps} style={{ whiteSpace: 'nowrap' }}>
                        {children}
                      </tr>
                    );
                  },
                },
              }}
              size="middle"
            />
          </div>
          <div style={{ 
            padding: '12px 16px', 
            background: '#fafafa', 
            borderTop: '1px solid #f0f0f0',
            textAlign: 'right',
            width: '100%'
          }}>
            Showing {filteredData.length} customers
          </div>
        </Card>
      </div>
    </div>
  );
};

export default ChurnPrediction;
