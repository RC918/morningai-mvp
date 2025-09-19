import { toast } from 'sonner';

export const useToast = () => {
  return {
    toast: (options) => {
      if (typeof options === 'string') {
        return toast(options);
      }
      
      const { title, description, variant = 'default', ...rest } = options;
      
      if (variant === 'destructive') {
        return toast.error(title, {
          description,
          ...rest
        });
      }
      
      return toast.success(title, {
        description,
        ...rest
      });
    }
  };
};
