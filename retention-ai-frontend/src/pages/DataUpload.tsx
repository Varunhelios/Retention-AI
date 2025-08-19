import React, { useState } from 'react';
import { Upload, Button, Row, Col, Typography, Tabs, Form, Input, InputNumber, Select, DatePicker, Slider, Collapse, Card, message } from 'antd';
import { UploadOutlined, InboxOutlined, UserAddOutlined, FileTextOutlined } from '@ant-design/icons';
import GridItem from '../components/ui/GridItem';
import apiClient from '../api/apiClient';

const { Dragger } = Upload;
const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const DataUpload: React.FC = () => {
  const [fileList, setFileList] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);
  const [submittingIndividual, setSubmittingIndividual] = useState(false);
  const [numDays, setNumDays] = useState<number>(30);
  const [form] = Form.useForm();
  const [messageApi, contextHolder] = message.useMessage();

  const handleUpload = async () => {
    if (fileList.length === 0) return;
    const formData = new FormData();
    // Backend expects a single field named 'file'
    formData.append('file', fileList[0] as any);

    try {
      setUploading(true);
      const res = await apiClient.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      const msg = res?.data?.message || 'Upload successful';
      const processed = res?.data?.records_processed;
      message.success(processed ? `${msg}. Records: ${processed}` : msg);
      setFileList([]);
    } catch (err: any) {
      console.error('Upload failed:', err);
      message.error(err?.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const props = {
    onRemove: (file: any) => {
      const index = fileList.indexOf(file);
      const newFileList = fileList.slice();
      newFileList.splice(index, 1);
      setFileList(newFileList);
    },
    beforeUpload: (file: any) => {
      // Check file type and size if needed
      const isCSV = file.type === 'text/csv' || file.name.endsWith('.csv');
      if (!isCSV) {
        message.error('You can only upload CSV files!');
        return Upload.LIST_IGNORE;
      }
      setFileList([...fileList, file]);
      return false;
    },
    fileList,
  };

  const handleIndividualSubmit = async (values: any) => {
    try {
      setSubmittingIndividual(true);
      
      // Build Day_1..Day_90 (default 0 when not provided)
      const dayFields: Record<string, number> = {};
      for (let i = 1; i <= 90; i++) {
        const k = `Day_${i}`;
        const v = values[k];
        dayFields[k] = typeof v === 'number' ? v : (v ? Number(v) : 0);
      }

      // Only include allowed fields per dataset
      const formattedData = {
        Average_Screen_Time: values.Average_Screen_Time,
        Average_Spent: values.Average_Spent,
        Ratings: values.Ratings,
        New_Password_Request: values.New_Password_Request || 0,
        Last_Visited_Minutes: values.Last_Visited_Minutes,
        review: values.review,
        ...dayFields,
      };
      
      const response = await apiClient.post('/add-individual-entry', formattedData);
      
      if (response.data.success) {
        messageApi.success(response.data.message || 'Individual entry added successfully.');
        form.resetFields();
        setNumDays(30);
        
        if (response.data.processing_success) {
          messageApi.info(response.data.processing_message);
        } else {
          messageApi.warning(`Entry saved but processing had issues: ${response.data.processing_message}`);
        }
      }
    } catch (error: any) {
      console.error('Individual entry error:', error);
      messageApi.error(error.response?.data?.detail || 'Failed to add individual entry');
    } finally {
      setSubmittingIndividual(false);
    }
  };

  const csvUploadTab = (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <GridItem title="Upload Customer Data">
          <Dragger {...props} multiple={false}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined style={{ fontSize: '48px', color: '#1890ff' }} />
            </p>
            <p className="ant-upload-text">
              Click or drag CSV file to this area to upload
            </p>
            <p className="ant-upload-hint">
              Support for a single CSV file upload. File should contain customer data with relevant features.
            </p>
          </Dragger>
          <div style={{ marginTop: 16, textAlign: 'right' }}>
            <Button
              type="primary"
              onClick={handleUpload}
              disabled={fileList.length === 0}
              loading={uploading}
              icon={<UploadOutlined />}
              size="large"
            >
              {uploading ? 'Uploading' : 'Start Upload'}
            </Button>
          </div>
        </GridItem>
      </Col>
    </Row>
  );

  const individualEntryTab = (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <GridItem title="Add Individual User Entry">
          <Form
            form={form}
            layout="vertical"
            onFinish={handleIndividualSubmit}
            style={{ maxWidth: '800px' }}
          >
            <Row gutter={[16, 16]}>
              {/* User ID removed; IDs are auto-assigned during processing */}
              
              <Col xs={24} md={12}>
                <Form.Item
                  label="Average Screen Time (minutes)"
                  name="Average_Screen_Time"
                  rules={[{ required: true, message: 'Please enter average screen time' }]}
                >
                  <InputNumber
                    min={0}
                    style={{ width: '100%' }}
                    placeholder="Average daily screen time in minutes"
                  />
                </Form.Item>
              </Col>
              
              <Col xs={24} md={12}>
                <Form.Item
                  label="Average Spent on App (INR)"
                  name="Average_Spent"
                  rules={[{ required: true, message: 'Please enter average amount spent' }]}
                >
                  <InputNumber
                    min={0}
                    style={{ width: '100%' }}
                    placeholder="Average amount spent in INR"
                  />
                </Form.Item>
              </Col>
              
              <Col xs={24} md={12}>
                <Form.Item
                  label="Ratings (1-5)"
                  name="Ratings"
                  rules={[{ required: true, message: 'Please enter rating' }]}
                >
                  <InputNumber
                    min={1}
                    max={5}
                    step={0.1}
                    style={{ width: '100%' }}
                    placeholder="Rating from 1 to 5"
                  />
                </Form.Item>
              </Col>
              
              <Col xs={24} md={12}>
                <Form.Item
                  label="Password Reset Requests"
                  name="New_Password_Request"
                  initialValue={0}
                >
                  <InputNumber
                    min={0}
                    style={{ width: '100%' }}
                    placeholder="Number of password reset requests"
                  />
                </Form.Item>
              </Col>
              
              <Col xs={24} md={12}>
                <Form.Item
                  label="Last Visited (minutes ago)"
                  name="Last_Visited_Minutes"
                  rules={[{ required: true, message: 'Please enter minutes since last visit' }]}
                >
                  <InputNumber
                    min={0}
                    style={{ width: '100%' }}
                    placeholder="Minutes since last visit"
                  />
                </Form.Item>
              </Col>
              
              <Col xs={24}>
                <Card size="small" style={{ borderRadius: 6 }}>
                  <Collapse defaultActiveKey={['usage']} bordered={false}>
                    <Collapse.Panel header={<strong>Daily Usage Data</strong>} key="usage">
                      <div style={{ marginBottom: 8 }}>Number of Days to Track: {numDays}</div>
                      <Slider
                        min={1}
                        max={90}
                        step={1}
                        value={numDays}
                        onChange={(v: number) => setNumDays(v)}
                        marks={{ 1: '1', 30: '30', 60: '60', 90: '90' }}
                        tooltip={{ formatter: (v?: number) => `${v} days` }}
                        style={{ maxWidth: 600 }}
                      />
                      <Row gutter={[8, 8]} style={{ marginTop: 16 }}>
                        {Array.from({ length: numDays }, (_, i) => i + 1).map((day) => (
                          <Col xs={12} sm={8} md={6} lg={4} xl={3} key={day}>
                            <Form.Item name={`Day_${day}`} label={`Day ${day}`}>
                              <InputNumber min={0} style={{ width: '100%' }} placeholder="0" />
                            </Form.Item>
                          </Col>
                        ))}
                      </Row>
                    </Collapse.Panel>
                  </Collapse>
                </Card>
              </Col>
              
              <Col xs={24}>
                <Form.Item
                  label="Review (Optional)"
                  name="review"
                  tooltip="User review text for sentiment analysis"
                >
                  <TextArea
                    rows={3}
                    placeholder="Optional: Leave a review about your experience"
                  />
                </Form.Item>
              </Col>
            </Row>
            
            <div style={{ marginTop: 24, textAlign: 'right' }}>
              <Button
                type="primary"
                htmlType="submit"
                loading={submittingIndividual}
                icon={<UserAddOutlined />}
                size="large"
              >
                {submittingIndividual ? 'Adding Entry...' : 'Add Individual Entry'}
              </Button>
            </div>
          </Form>
        </GridItem>
      </Col>
    </Row>
  );

  return (
    <>
      {contextHolder}
      <div className="data-upload">
      <Title level={2}>Data Upload</Title>
      
      <Tabs
        defaultActiveKey="csv"
        size="large"
        items={[
          {
            key: 'csv',
            label: (
              <span>
                <FileTextOutlined />
                CSV Upload
              </span>
            ),
            children: csvUploadTab
          },
          {
            key: 'individual',
            label: (
              <span>
                <UserAddOutlined />
                Individual Entry
              </span>
            ),
            children: individualEntryTab
          }
        ]}
      />
      
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col span={24}>
          <GridItem title="Data Format Requirements">
            <div style={{ padding: '16px', backgroundColor: '#f9f9f9', borderRadius: '6px' }}>
              <Text strong>Required Fields:</Text>
              <ul style={{ marginTop: '8px', paddingLeft: '20px' }}>
                <li><Text code>Average_Screen_Time</Text>: Daily average in minutes (e.g., 45.5)</li>
                <li><Text code>Average_Spent</Text>: Average amount spent in INR (e.g., 299.99)</li>
                <li><Text code>Ratings</Text>: User rating from 1 to 5 (e.g., 4.5)</li>
                <li><Text code>New_Password_Request</Text>: Count of password reset requests (e.g., 2)</li>
                <li><Text code>Last_Visited_Minutes</Text>: Minutes since last visit (e.g., 120)</li>
              </ul>
              <Text strong style={{ marginTop: '12px', display: 'block' }}>Optional Fields:</Text>
              <ul style={{ marginTop: '8px', paddingLeft: '20px' }}>
                <li><Text code>review</Text>: User review text (for sentiment analysis)</li>
                <li><Text code>Day_1 to Day_90</Text>: Daily usage in minutes (e.g., 45, 60, 30)</li>
              </ul>
            </div>
          </GridItem>
        </Col>
      </Row>
    </div>
    </>
  );
};

export default DataUpload;
