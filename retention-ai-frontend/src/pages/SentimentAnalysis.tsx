import React, { useState, useEffect } from 'react';
import { Table, Tag, Input, message } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import GridItem from '../components/ui/GridItem';
import { sentimentAPI } from '../services/api';

// Define the data structure
interface SentimentData {
  key: string;
  userid: string;
  review: string;
  compound_score: string;
  sentiment: 'positive' | 'neutral' | 'negative';
}

const columns = [
  {
    title: 'User ID',
    dataIndex: 'userid',
    key: 'userid',
    width: '15%',
  },
  {
    title: 'Review',
    dataIndex: 'review',
    key: 'review',
    width: '60%',
    render: (text: string) => (
      <div style={{ 
        whiteSpace: 'normal',
        wordWrap: 'break-word',
        maxHeight: '200px',
        overflowY: 'auto',
        padding: '8px 0'
      }}>
        {text}
      </div>
    ),
  },
  {
    title: 'Sentiment',
    dataIndex: 'sentiment',
    key: 'sentiment',
    width: '15%',
    render: (sentiment: string) => {
      const color = sentiment === 'positive' ? 'green' : sentiment === 'negative' ? 'red' : 'orange';
      return (
        <Tag color={color} key={sentiment}>
          {sentiment.toUpperCase()}
        </Tag>
      );
    },
    filters: [
      { text: 'Positive', value: 'positive' },
      { text: 'Negative', value: 'negative' },
      { text: 'Neutral', value: 'neutral' },
    ],
    onFilter: (value: any, record: SentimentData) => record.sentiment === value,
  },
  {
    title: 'Score',
    dataIndex: 'compound_score',
    key: 'score',
    width: '10%',
    sorter: (a: SentimentData, b: SentimentData) => 
      parseFloat(a.compound_score) - parseFloat(b.compound_score),
    render: (score: string) => parseFloat(score).toFixed(4)
  },
];

const SentimentAnalysis: React.FC = () => {
  const [sentimentData, setSentimentData] = useState<SentimentData[]>([]);
  const [filteredData, setFilteredData] = useState<SentimentData[]>([]);
  const [searchText, setSearchText] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const response = await sentimentAPI.getSentimentData();
        
        // Process the data to match our interface
        const processedData = response.data.map((item: any, index: number) => ({
          ...item,
          key: index.toString(),
          sentiment: parseFloat(item.compound_score) > 0.05 ? 'positive' : 
                    parseFloat(item.compound_score) < -0.05 ? 'negative' : 'neutral'
        }));
        
        setSentimentData(processedData);
        setFilteredData(processedData);
      } catch (error) {
        console.error('Error loading sentiment data:', error);
        message.error('Failed to load sentiment data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  useEffect(() => {
    if (searchText.trim() === '') {
      setFilteredData(sentimentData);
    } else {
      const searchLower = searchText.toLowerCase();
      const filtered = sentimentData.filter(item => 
        String(item.userid || '').toLowerCase().includes(searchLower)
      );
      setFilteredData(filtered);
    }
  }, [searchText, sentimentData]);

  return (
    <div className="sentiment-analysis" style={{ padding: 0, margin: 0, height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '24px 24px 0' }}>
        <h1 style={{ margin: 0, paddingBottom: '16px' }}>Sentiment Analysis</h1>
      </div>
      
      <div style={{ flex: 1, padding: '0 24px 24px', display: 'flex', flexDirection: 'column' }}>
        <GridItem 
          title="Customer Sentiment Analysis" 
          style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
        >
          <div style={{ marginBottom: 16, padding: '0 8px' }}>
            <Input
              placeholder="Search by User ID..."
              prefix={<SearchOutlined />}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchText(e.target.value)}
              style={{ width: 300, marginBottom: 16 }}
              allowClear
            />
          </div>
          <div style={{ 
            flex: 1,
            width: '100%',
            display: 'flex', 
            flexDirection: 'column',
            overflow: 'hidden',
            margin: 0,
            padding: 0,
            maxHeight: 'calc(100vh - 200px)'
          }}>
            <div style={{ 
              flex: 1, 
              overflow: 'auto',
              width: '100%'
            }}>
              <Table 
                columns={columns} 
                dataSource={filteredData}
                loading={loading}
                pagination={false}
                scroll={{ y: '100%' }}
                style={{ width: '100%', height: '100%', tableLayout: 'fixed' }}
                bordered
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
              width: '100%',
              margin: '0 -16px',
              paddingRight: '16px'
            }}>
              Showing {filteredData.length} reviews
            </div>
          </div>
        </GridItem>
      </div>
    </div>
  );
};

export default SentimentAnalysis;
