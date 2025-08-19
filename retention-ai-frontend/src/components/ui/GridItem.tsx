import React from 'react';
import { Card } from 'antd';

interface GridItemProps {
  title: React.ReactNode; // Changed from string to ReactNode to support JSX elements
  children: React.ReactNode;
  style?: React.CSSProperties;
}

const GridItem: React.FC<GridItemProps> = ({ title, children, style = {} }) => {
  return (
    <Card 
      title={title} 
      style={{ 
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
        height: '100%',
        ...style 
      }}
      headStyle={{ 
        borderBottom: '1px solid #f0f0f0',
        fontWeight: 500 
      }}
    >
      {children}
    </Card>
  );
};

export default GridItem;
