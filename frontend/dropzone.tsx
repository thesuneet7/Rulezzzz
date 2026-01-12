
import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Shield, FileText, Settings, UploadCloud } from 'lucide-react';

interface DropzoneProps {
    onFileChange: (file: File | null) => void;
    title: string;
    description: string;
    iconType: 'shield' | 'file' | 'settings';
    accept?: Record<string, string[]>;
}

const Dropzone: React.FC<DropzoneProps> = ({ onFileChange, title, description, iconType }) => {
    const [fileName, setFileName] = useState<string | null>(null);

    const onDrop = useCallback((acceptedFiles: File[]) => {
        if (acceptedFiles.length > 0) {
            const file = acceptedFiles[0];
            setFileName(file.name);
            onFileChange(file);
        }
    }, [onFileChange]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        multiple: false
    });

    const getIcon = () => {
        switch (iconType) {
            case 'shield': return <Shield size={32} color="#2563EB" />;
            case 'file': return <FileText size={32} color="#2563EB" />;
            case 'settings': return <Settings size={32} color="#2563EB" />;
            default: return <UploadCloud size={32} color="#2563EB" />;
        }
    };

    return (
        <div
            {...getRootProps()}
            className={`dropzone-card ${isDragActive ? 'active' : ''}`}
            style={{
                background: '#fff',
                border: '1px dashed #E5E7EB',
                borderRadius: '16px',
                padding: '3rem 2rem',
                textAlign: 'center',
                cursor: 'pointer',
                transition: 'all 0.2s',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                boxShadow: fileName ? '0 0 0 2px #2563EB' : 'none'
            }}
        >
            <input {...getInputProps()} />
            <div style={{
                background: '#EFF6FF',
                padding: '16px',
                borderRadius: '16px',
                marginBottom: '1.5rem',
                display: 'inline-flex'
            }}>
                {getIcon()}
            </div>

            {fileName ? (
                <div>
                    <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem' }}>File Selected</h3>
                    <p style={{ color: '#2563EB', fontWeight: 600, margin: 0 }}>{fileName}</p>
                </div>
            ) : (
                <>
                    <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem', fontWeight: 600 }}>{title}</h3>
                    <p style={{ color: '#6B7280', fontSize: '0.9rem', margin: 0, lineHeight: 1.5 }}>
                        {description}
                    </p>
                </>
            )}
        </div>
    );
};

export default Dropzone;
