import { Modal, ModalHeader, ModalTitle, ModalContent, ModalFooter } from './modal';
import { Button } from './button';
import { AlertTriangle } from 'lucide-react';

interface ConfirmationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'warning' | 'info';
  isLoading?: boolean;
}

export function ConfirmationDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  description,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'danger',
  isLoading = false
}: ConfirmationDialogProps) {
  const handleConfirm = () => {
    onConfirm();
  };

  const getVariantStyles = () => {
    switch (variant) {
      case 'danger':
        return {
          icon: 'text-red-600',
          confirmButton: 'bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white border-red-600 hover:border-red-700 disabled:border-red-400'
        };
      case 'warning':
        return {
          icon: 'text-yellow-600',
          confirmButton: 'bg-yellow-600 hover:bg-yellow-700 disabled:bg-yellow-400 text-white border-yellow-600 hover:border-yellow-700 disabled:border-yellow-400'
        };
      default:
        return {
          icon: 'text-blue-600',
          confirmButton: 'bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white border-blue-600 hover:border-blue-700 disabled:border-blue-400'
        };
    }
  };

  const styles = getVariantStyles();

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <ModalHeader>
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-full ${variant === 'danger' ? 'bg-red-100' : variant === 'warning' ? 'bg-yellow-100' : 'bg-blue-100'}`}>
            <AlertTriangle className={`h-5 w-5 ${styles.icon}`} />
          </div>
          <ModalTitle>{title}</ModalTitle>
        </div>
      </ModalHeader>
      
      <ModalContent>
        <p className="text-gray-600 leading-relaxed">
          {description}
        </p>
      </ModalContent>
      
      <ModalFooter>
        <Button
          onClick={onClose}
          disabled={isLoading}
          className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium px-4 py-2 rounded-lg shadow-sm border border-gray-300 hover:border-gray-400 transition-all duration-200"
        >
          {cancelText}
        </Button>
        <Button
          onClick={handleConfirm}
          disabled={isLoading}
          className={`font-medium px-4 py-2 rounded-lg shadow-sm transition-all duration-200 hover:shadow-md disabled:cursor-not-allowed ${styles.confirmButton}`}
        >
          {isLoading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Deleting...
            </>
          ) : (
            confirmText
          )}
        </Button>
      </ModalFooter>
    </Modal>
  );
}