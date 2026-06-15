"use client";

import * as React from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { useRouter } from 'next/navigation';
import { Check, AlertTriangle, Eye, EyeOff } from "lucide-react";
import { login } from "@/lib/api";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";

const sqlAuthSchema = z.object({
  server: z.string().min(1, "Server IP is required"),
  database: z.string().min(1, "Database Name is required"),
  username: z.string().min(1, "Username is required"),
  password: z.string().min(1, "Password is required"),
  rememberServer: z.boolean().default(false),
  auth_type: z.literal("sql"),
});

const windowsAuthSchema = z.object({
  server: z.string().min(1, "Server IP is required"),
  database: z.string().min(1, "Database Name is required"),
  username: z.string().min(1, "Username is required (domain\\user)"),
  rememberServer: z.boolean().default(false),
  auth_type: z.literal("windows"),
});

const authSchema = z.union([sqlAuthSchema, windowsAuthSchema]);

type AuthFormType = z.infer<typeof authSchema>;

export function LoginForm() {
  const router = useRouter();
  const { toast } = useToast();
  const [authType, setAuthType] = React.useState<"sql" | "windows">("sql");
  const [showPassword, setShowPassword] = React.useState(false);

  const form = useForm<AuthFormType>({
    resolver: zodResolver(authSchema),
    defaultValues: authType === "sql" 
      ? { server: "", database: "", username: "", password: "", rememberServer: false, auth_type: "sql" }
      : { server: "", database: "", username: "", rememberServer: false, auth_type: "windows" },
    mode: "onChange",
  });

  React.useEffect(() => {
    const savedServer = localStorage.getItem('scada_server') || "";
    const savedDb = localStorage.getItem('scada_database') || "";
    const hasSaved = !!(savedServer || savedDb);
    
    const values = authType === "sql"
      ? { server: savedServer, database: savedDb, username: "", password: "", rememberServer: hasSaved, auth_type: "sql" as const }
      : { server: savedServer, database: savedDb, username: "", rememberServer: hasSaved, auth_type: "windows" as const };
    form.reset(values);
  }, [authType, form]);

  const onSubmit = async (values: AuthFormType) => {
    form.clearErrors();
    toast({
      title: "Login Attempt",
      description: `Authenticating as ${values.username}...`,
    });
    try {
      const loginData = {
        auth_type: values.auth_type,
        server: values.server.trim(),
        database: values.database.trim(),
        username: values.username.trim(),
        ...(values.auth_type === "sql" ? {
          password: (values as z.infer<typeof sqlAuthSchema>).password,
        } : {})
      };
      
      if (values.rememberServer) {
        localStorage.setItem('scada_server', values.server.trim());
        localStorage.setItem('scada_database', values.database.trim());
      } else {
        localStorage.removeItem('scada_server');
        localStorage.removeItem('scada_database');
      }
      
      const res = await login(loginData);
      
      if (res?.data?.success) {
        toast({
          title: "Login Successful",
          description: "Redirecting to dashboard...",
          variant: "default",
        });
        if (res.data.token) {
          localStorage.setItem('auth_token', res.data.token);
          document.cookie = `auth_token=${res.data.token}; path=/; max-age=86400; SameSite=Lax`;
        }
        router.push("/dashboard");
      } else {
        throw new Error(res?.data?.detail || "Invalid response from server");
      }
    } catch (err: any) {
      console.error("Login error:", err);
      let errorMessage = "Authentication failed";
      
      if (err?.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err?.message?.includes("Network Error")) {
        errorMessage = "Cannot connect to the server. Please check if the server is running.";
      } else if (err?.message) {
        errorMessage = err.message;
      }
      
      toast({
        title: "Login Failed",
        description: errorMessage,
        variant: "destructive"
      });
      
      if (values.auth_type === "sql") {
        form.setValue("password", "");
      }
    }
  };

  const getFieldStateIcon = (fieldName: "username" | "password") => {
    if (authType === "sql" && ["username", "password"].includes(fieldName)) {
      const fieldState = form.getFieldState(fieldName);
      if (!fieldState.isDirty) return null;
      if (fieldState.error) {
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      }
      if (form.getValues(fieldName)) {
        return <Check className="h-4 w-4 text-green-500" />;
      }
    } else if (authType === "windows" && fieldName === "username") {
      const fieldState = form.getFieldState(fieldName);
      if (!fieldState.isDirty) return null;
      if (fieldState.error) {
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      }
      if (form.getValues(fieldName)) {
        return <Check className="h-4 w-4 text-green-500" />;
      }
    }
    return null;
  };

  return (
    <Tabs value={authType} onValueChange={(value) => setAuthType(value as AuthFormType["auth_type"])} className="w-full">
      <TabsList className="grid w-full grid-cols-2 mb-6 bg-slate-100/80 dark:bg-slate-900/80 p-1 rounded-xl">
        <TabsTrigger 
          value="sql" 
          className="rounded-lg py-2 text-xs font-bold text-slate-500 dark:text-slate-400 transition-all data-[state=active]:bg-white dark:data-[state=active]:bg-slate-950 data-[state=active]:text-slate-900 dark:data-[state=active]:text-slate-150 data-[state=active]:shadow-sm"
        >
          SQL Server
        </TabsTrigger>
        <TabsTrigger 
          value="windows" 
          className="rounded-lg py-2 text-xs font-bold text-slate-500 dark:text-slate-400 transition-all data-[state=active]:bg-white dark:data-[state=active]:bg-slate-950 data-[state=active]:text-slate-900 dark:data-[state=active]:text-slate-150 data-[state=active]:shadow-sm"
        >
          Windows
        </TabsTrigger>
      </TabsList>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
          <div className="grid grid-cols-2 gap-4">
            <FormField
              control={form.control}
              name="server"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-[10px] font-bold text-slate-500 dark:text-slate-400 tracking-wider uppercase">Server IP</FormLabel>
                  <FormControl>
                    <Input placeholder="192.168.1.100" {...field} className="h-11 text-xs rounded-xl" />
                  </FormControl>
                  <FormMessage className="text-[10px]" />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="database"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-[10px] font-bold text-slate-500 dark:text-slate-400 tracking-wider uppercase">Database</FormLabel>
                  <FormControl>
                    <Input placeholder="SCADA_DB" {...field} className="h-11 text-xs rounded-xl" />
                  </FormControl>
                  <FormMessage className="text-[10px]" />
                </FormItem>
              )}
            />
          </div>
          <FormField
            control={form.control}
            name="username"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-[10px] font-bold text-slate-500 dark:text-slate-400 tracking-wider uppercase">Username</FormLabel>
                <div className="relative">
                  <FormControl>
                    <Input 
                      placeholder={authType === 'sql' ? "e.g., sa" : "e.g., DOMAIN\\user"} 
                      {...field} 
                      className={cn(
                        "bg-slate-50/50 dark:bg-slate-900/40 border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 focus:bg-white dark:focus:bg-slate-950 focus:ring-4 focus:ring-blue-500/5 focus:border-blue-500 dark:focus:border-blue-400 rounded-xl h-11 text-xs transition-all duration-200", 
                        form.getFieldState("username").error && "border-red-300 dark:border-red-800 focus:ring-red-500/5 focus:border-red-500"
                      )} 
                    />
                  </FormControl>
                  <div className="absolute inset-y-0 right-3 flex items-center">
                    {getFieldStateIcon("username")}
                  </div>
                </div>
                <FormMessage className="text-[10px] text-red-500" />
              </FormItem>
            )}
          />
          {authType === "sql" && (
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-[10px] font-bold text-slate-500 dark:text-slate-400 tracking-wider uppercase">Password</FormLabel>
                  <div className="relative">
                    <FormControl>
                      <Input 
                        type={showPassword ? "text" : "password"} 
                        placeholder="••••••••" 
                        {...field} 
                        className={cn(
                          "bg-slate-50/50 dark:bg-slate-900/40 border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 pr-10 focus:bg-white dark:focus:bg-slate-950 focus:ring-4 focus:ring-blue-500/5 focus:border-blue-500 dark:focus:border-blue-400 rounded-xl h-11 text-xs transition-all duration-200", 
                          form.getFieldState("password").error && "border-red-300 dark:border-red-800 focus:ring-red-500/5 focus:border-red-500"
                        )} 
                      />
                    </FormControl>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="absolute inset-y-0 right-0 h-full px-3 text-slate-455 hover:text-slate-655 hover:bg-transparent"
                      onClick={() => setShowPassword(!showPassword)}
                      aria-label={showPassword ? "Hide password" : "Show password"}
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                    <div className="absolute inset-y-0 right-10 flex items-center">
                      {getFieldStateIcon("password")}
                    </div>
                  </div>
                  <FormMessage className="text-[10px] text-red-500" />
                </FormItem>
              )}
            />
          )}
          <FormField
            control={form.control}
            name="rememberServer"
            render={({ field }) => (
              <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-md py-2">
                <FormControl>
                  <Checkbox
                    checked={field.value}
                    onCheckedChange={field.onChange}
                  />
                </FormControl>
                <div className="space-y-1 leading-none">
                  <FormLabel className="text-xs text-slate-500 cursor-pointer">
                    Remember server details
                  </FormLabel>
                </div>
              </FormItem>
            )}
          />
          <Button 
            type="submit" 
            className="w-full h-11 text-xs uppercase font-extrabold tracking-wider bg-blue-600 hover:bg-blue-700 text-white dark:bg-blue-600 dark:hover:bg-blue-500 rounded-xl shadow-sm hover:shadow-md hover:shadow-blue-500/10 active:scale-[0.98] transition-all duration-200 mt-2" 
            disabled={!form.formState.isValid || form.formState.isSubmitting}
          >
            {form.formState.isSubmitting ? "Processing..." : "Proceed"}
          </Button>
        </form>
      </Form>
    </Tabs>
  );
}
